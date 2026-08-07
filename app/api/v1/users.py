# app/api/v1/users.py (НОВЫЙ ФАЙЛ)
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.user import UserResponse, UserUpdate, user_to_response
from app.schemas.auth import ChangePasswordRequest
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.services.token_service import TokenService
from app.repositories.blacklist_repo import BlacklistRepository
from app.repositories.refresh_repo import RefreshTokenRepository
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


# ========== Вспомогательные функции ==========

async def get_user_service(db) -> UserService:
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    return UserService(user_repo, role_repo)


async def get_auth_service(db) -> AuthService:
    user_repo = UserRepository(db)
    blacklist_repo = BlacklistRepository(db)
    refresh_repo = RefreshTokenRepository(db)
    token_service = TokenService(blacklist_repo, refresh_repo, user_repo)
    # email_service = EmailService()  # если нужен
    return AuthService(user_repo, token_service, None)  # email_service можно добавить


# ========== Профиль пользователя ==========

@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Получение информации о текущем пользователе
    """
    user_service = await get_user_service(db)
    
    projects = await current_user.awaitable_attrs.projects
    roles = await current_user.awaitable_attrs.roles
    
    project_titles = [p.project_title for p in projects] if projects else []
    role_titles = [r.role_title for r in roles] if roles else []
    
    return user_to_response(current_user, role_titles, project_titles)


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Обновление информации о текущем пользователе
    """
    user_service = await get_user_service(db)
    
    # Запрещаем обновление чувствительных полей
    update_dict = update_data.model_dump(exclude_unset=True)
    forbidden = ['user_name', 'email']  # Нельзя изменить username и email без доп. проверки
    
    for field in forbidden:
        update_dict.pop(field, None)
    
    user = await user_service.update_user(current_user.user_id, update_dict)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/me/change-password")
async def change_my_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Изменение пароля текущего пользователя
    """
    auth_service = await get_auth_service(db)
    return await auth_service.change_password(current_user.user_id, request)


@router.get("/me/status")
async def get_my_status(
    current_user: User = Depends(get_current_user)
):
    """
    Получение статуса текущего пользователя
    """
    from app.schemas.user import get_user_status_from_model
    
    return {
        "user_id": current_user.user_id,
        "user_name": current_user.user_name,
        "email": current_user.email,
        "status": get_user_status_from_model(current_user),
        "is_blocked": current_user.blocked_at is not None,
        "is_deleted": current_user.deleted_at is not None,
        "blocked_reason": current_user.blocked_reason,
        "block_expires_at": current_user.block_expires_at,
        "deleted_at": current_user.deleted_at,
    }


# ========== Пользователи (публичные эндпоинты) ==========

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Получение списка пользователей (только активные)
    """
    user_service = await get_user_service(db)
    
    users = await user_service.get_all_users(skip, limit, only_active=True)
    
    # Фильтр по поиску если нужен
    if search:
        users = [u for u in users if search.lower() in u.user_name.lower() or 
                 (u.email and search.lower() in u.email.lower())]
    
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Получение информации о пользователе по ID (только активные)
    """
    user_service = await get_user_service(db)
    
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.get("/by-username/{username}", response_model=UserResponse)
async def get_user_by_username(
    username: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Получение информации о пользователе по имени
    """
    user_service = await get_user_service(db)
    
    user = await user_service.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    projects = await user.awaitable_attrs.projects
    roles = await user.awaitable_attrs.roles
    
    project_titles = [p.project_title for p in projects] if projects else []
    role_titles = [r.role_title for r in roles] if roles else []
    
    return user_to_response(user, role_titles, project_titles)


# ========== Управление сессиями ==========

@router.post("/me/logout-all")
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Выход из всех устройств (отзыв всех refresh токенов)
    """
    from app.services.token_service import TokenService
    from app.repositories.blacklist_repo import BlacklistRepository
    from app.repositories.refresh_repo import RefreshTokenRepository
    
    blacklist_repo = BlacklistRepository(db)
    refresh_repo = RefreshTokenRepository(db)
    user_repo = UserRepository(db)
    token_service = TokenService(blacklist_repo, refresh_repo, user_repo)
    
    revoked_count = await token_service.revoke_all_user_refresh_tokens(current_user.user_id)
    
    return {
        "message": f"Logged out from all devices",
        "revoked_tokens": revoked_count
    }
