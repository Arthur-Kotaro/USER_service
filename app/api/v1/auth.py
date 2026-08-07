# app/api/v1/auth.py (исправленная версия с импортами)
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.schemas.auth import (
    LoginRequest, TokenResponse, ChangePasswordRequest,
    PasswordExpiryResponse, PasswordResetRequest
)
from app.schemas.user import UserResponse  # ДОБАВИТЬ ЭТУ СТРОКУ
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service, get_current_user
from app.database import get_db  # Добавить эту строку в импорты
from app.models.user import User

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Аутентификация пользователя.
    Получает email и пароль, возвращает access и refresh токены.
    """
    return await auth_service.login(request, http_request)


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Изменение пароля авторизованного пользователя.
    Требует текущий пароль и новый пароль.
    """
    return await auth_service.change_password(current_user.user_id, request)


@router.get("/password-expiry", response_model=PasswordExpiryResponse)
async def get_password_expiry(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Получение информации о сроке действия пароля.
    """
    return await auth_service.get_password_expiry_info(current_user.user_id)


@router.post("/reset-password")
async def reset_password(
    request: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Запрос на сброс пароля.
    Отправляет временный пароль на email пользователя.
    """
    return await auth_service.request_password_reset(request)


@router.post("/refresh")
async def refresh_token(
    request: dict,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Обновление access токена с использованием refresh токена.
    """
    refresh_token = request.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token required")
    return await auth_service.refresh_token(refresh_token)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    refresh_token: str = None
):
    """
    Выход из системы.
    Отзывает refresh токен (если предоставлен) или все токены пользователя.
    """
    if refresh_token:
        await auth_service.revoke_refresh_token(refresh_token)
    else:
        await auth_service.revoke_all_user_refresh_tokens(current_user.user_id)
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)  # Нужно добавить импорт get_db
):
    """
    Получение информации о текущем авторизованном пользователе.
    """
    from app.schemas.user import user_to_response
    
    # Загружаем роли и проекты
    projects = await current_user.awaitable_attrs.projects
    roles = await current_user.awaitable_attrs.roles
    
    project_titles = [p.project_title for p in projects] if projects else []
    role_titles = [r.role_title for r in roles] if roles else []
    
    return user_to_response(current_user, role_titles, project_titles)


@router.get("/me/status")
async def get_my_status(
    current_user: User = Depends(get_current_user)
):
    """
    Получение детального статуса текущего пользователя.
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
