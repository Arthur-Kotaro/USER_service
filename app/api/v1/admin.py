# app/api/v1/admin.py (ОБНОВЛЁННАЯ ВЕРСИЯ)
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.schemas.admin import (
    UserAdminUpdate,
    UserAdminResponse,
    UserListResponse,
    AdminStatsResponse,
    BlockUserRequest,
    UnblockUserRequest,
    SoftDeleteUserRequest,
    RestoreUserRequest
)
from app.schemas.user import UserResponse
from app.services.admin_service import AdminService
from app.services.user_service import UserService
from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.login_history_repo import LoginHistoryRepository
from app.models.user import User
from app.utils.hasher import hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])


# ========== Вспомогательные функции ==========

async def get_admin_service(db) -> AdminService:
    """Dependency для AdminService"""
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    login_history_repo = LoginHistoryRepository(db)
    return AdminService(user_repo, role_repo, login_history_repo)


async def get_user_service(db) -> UserService:
    """Dependency для UserService"""
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    return UserService(user_repo, role_repo)


# ========== Управление пользователями ==========

@router.post("/users", response_model=UserAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserAdminUpdate,
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Создание нового пользователя (только администратор)
    """
    admin_service = await get_admin_service(db)
    
    # Проверка на существование
    if user_data.user_name:
        existing = await admin_service.get_user_by_username(user_data.user_name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
    
    if user_data.email:
        existing_email = await admin_service.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Генерируем временный пароль
    temp_password = UserService.generate_temp_password()  # Нужно добавить метод
    hashed_password = hash_password(temp_password)
    
    user = await admin_service.create_user(user_data, hashed_password)
    
    # TODO: Отправить email с временным паролем
    
    return user


@router.get("/users", response_model=UserListResponse)
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, pattern="^(active|blocked|deleted)$"),
    search: Optional[str] = None,
    include_deleted: bool = Query(False, description="Включить удалённых пользователей"),
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Получение списка пользователей с фильтрацией и пагинацией
    """
    admin_service = await get_admin_service(db)
    
    users, total = await admin_service.get_all_users(
        skip=skip, 
        limit=limit, 
        status_filter=status_filter,
        search=search,
        include_deleted=include_deleted
    )
    
    return UserListResponse(
        total=total,
        users=users
    )


@router.get("/users/{user_id}", response_model=UserAdminResponse)
async def get_user_by_id(
    user_id: int,
    include_deleted: bool = Query(False, description="Показать удалённого пользователя"),
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Получение информации о пользователе по ID
    """
    admin_service = await get_admin_service(db)
    user = await admin_service.get_user_by_id(user_id, include_deleted=include_deleted)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Загружаем роли и проекты
    roles = await user.awaitable_attrs.roles
    projects = await user.awaitable_attrs.projects
    role_titles = [r.role_title for r in roles] if roles else []
    project_titles = [p.project_title for p in projects] if projects else []
    
    from app.schemas.admin import user_to_admin_response
    return user_to_admin_response(user, role_titles, project_titles)


@router.put("/users/{user_id}", response_model=UserAdminResponse)
async def update_user(
    user_id: int,
    user_data: UserAdminUpdate,
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Обновление данных пользователя
    """
    admin_service = await get_admin_service(db)
    
    user = await admin_service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    roles = await user.awaitable_attrs.roles
    projects = await user.awaitable_attrs.projects
    role_titles = [r.role_title for r in roles] if roles else []
    project_titles = [p.project_title for p in projects] if projects else []
    
    from app.schemas.admin import user_to_admin_response
    return user_to_admin_response(user, role_titles, project_titles)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    soft: bool = Query(True, description="True - мягкое удаление, False - физическое"),
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Удаление пользователя
    - soft=True: мягкое удаление (установка deleted_at)
    - soft=False: физическое удаление из БД
    """
    admin_service = await get_admin_service(db)
    
    # Нельзя удалить самого себя
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    deleted = await admin_service.delete_user(user_id, soft=soft)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    action = "soft-deleted" if soft else "permanently deleted"
    return {"message": f"User {action} successfully", "user_id": user_id, "soft": soft}


@router.post("/users/{user_id}/restore")
async def restore_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Восстановление мягко удалённого пользователя
    """
    admin_service = await get_admin_service(db)
    
    user = await admin_service.restore_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or not deleted"
        )
    
    return {"message": f"User {user.user_name} restored successfully", "user_id": user_id}


# ========== Блокировка пользователей ==========

@router.post("/users/{user_id}/block")
async def block_user(
    user_id: int,
    block_data: BlockUserRequest,
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Блокировка пользователя
    """
    admin_service = await get_admin_service(db)
    
    # Нельзя заблокировать самого себя
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot block your own account"
        )
    
    user = await admin_service.block_user(
        user_id=user_id,
        admin_id=current_user.user_id,
        reason=block_data.reason,
        expires_at=block_data.expires_at
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "message": f"User {user.user_name} blocked successfully",
        "user_id": user_id,
        "blocked_at": datetime.utcnow(),
        "reason": block_data.reason,
        "expires_at": block_data.expires_at
    }


@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    unblock_data: Optional[UnblockUserRequest] = None,
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Разблокировка пользователя
    """
    admin_service = await get_admin_service(db)
    
    user = await admin_service.unblock_user(
        user_id, 
        admin_id=current_user.user_id,
        reason=unblock_data.reason if unblock_data else None
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "message": f"User {user.user_name} unblocked successfully",
        "user_id": user_id
    }


# ========== Управление ролями ==========

@router.post("/users/{user_id}/roles")
async def assign_role(
    user_id: int,
    role_data: dict,  # {"role_id": int} или {"role_code": str}
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Назначение роли пользователю
    Можно указать либо role_id, либо role_code
    """
    admin_service = await get_admin_service(db)
    
    # Проверка существования пользователя
    user = await admin_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = False
    if "role_id" in role_data:
        success = await admin_service.assign_role(user_id, role_data["role_id"])
    elif "role_code" in role_data:
        success = await admin_service.assign_role_by_code(user_id, role_data["role_code"])
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either role_id or role_code required"
        )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign role (role may not exist)"
        )
    
    return {"message": "Role assigned successfully"}


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Удаление роли у пользователя
    """
    admin_service = await get_admin_service(db)
    
    success = await admin_service.remove_role(user_id, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove role (user or role may not exist)"
        )
    
    return {"message": "Role removed successfully"}


@router.get("/users/{user_id}/roles")
async def get_user_roles(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Получение списка ролей пользователя
    """
    admin_service = await get_admin_service(db)
    
    user = await admin_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    roles = await user.awaitable_attrs.roles
    return [
        {
            "role_id": r.role_id,
            "role_title": r.role_title,
            "role_title_ru": r.role_title_ru,
            "role_code": r.role_code
        }
        for r in roles
    ]


# ========== Управление проектами ==========

@router.post("/users/{user_id}/projects")
async def assign_project(
    user_id: int,
    project_data: dict,  # {"project_id": int, "project_role": str}
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Назначение проекта пользователю
    """
    admin_service = await get_admin_service(db)
    
    success = await admin_service.assign_project(
        user_id, 
        project_data.get("project_id"),
        project_data.get("project_role", "member")
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign project"
        )
    
    return {"message": "Project assigned successfully"}


@router.delete("/users/{user_id}/projects/{project_id}")
async def remove_project(
    user_id: int,
    project_id: int,
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Удаление проекта у пользователя
    """
    admin_service = await get_admin_service(db)
    
    success = await admin_service.remove_project(user_id, project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove project"
        )
    
    return {"message": "Project removed successfully"}


# ========== История входов ==========

@router.get("/users/{user_id}/login-history")
async def get_user_login_history(
    user_id: int,
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Получение истории входов пользователя
    """
    admin_service = await get_admin_service(db)
    
    history = await admin_service.get_user_login_history(user_id, limit)
    return {"user_id": user_id, "history": history}


# ========== Статистика ==========

@router.get("/stats/overview", response_model=AdminStatsResponse)
async def get_admin_stats(
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Получение статистики для администратора
    """
    admin_service = await get_admin_service(db)
    stats = await admin_service.get_stats()
    return stats


@router.get("/stats/daily-registrations")
async def get_daily_registrations(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Получение статистики регистраций по дням
    """
    admin_service = await get_admin_service(db)
    stats = await admin_service.get_daily_registrations(days)
    return {"days": days, "data": stats}
