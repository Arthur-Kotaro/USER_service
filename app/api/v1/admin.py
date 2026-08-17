# app/api/v1/admin.py (ОБНОВЛЕННАЯ ВЕРСИЯ - БЕЗ ПРОЕКТОВ)
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.dependencies import get_current_admin
from app.schemas.admin import (
    UserAdminUpdate,
    UserAdminResponse,
    UserListResponse,
    AdminStatsResponse,
    BlockUserRequest,
    UnblockUserRequest,
)
from app.services.admin_service import AdminService
from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.login_history_repo import LoginHistoryRepository
from app.models.user import User

router = APIRouter(tags=["Admin"])


# ========== Вспомогательные функции ==========

async def get_admin_service(db) -> AdminService:
    """Dependency для AdminService"""
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    login_history_repo = LoginHistoryRepository(db)
    return AdminService(user_repo, role_repo, login_history_repo)


# ========== Управление пользователями ==========

@router.get("/users", response_model=UserListResponse)
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_deleted: bool = Query(False, description="Включить удалённых пользователей"),
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Получение списка пользователей с пагинацией
    """
    admin_service = await get_admin_service(db)
    return await admin_service.get_users(skip, limit, include_deleted)


@router.get("/users/{user_id}", response_model=UserAdminResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Получение информации о пользователе по ID
    """
    admin_service = await get_admin_service(db)
    user = await admin_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


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
    
    user = await admin_service.update_user_by_admin(user_id, user_data, current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Мягкое удаление пользователя
    """
    admin_service = await get_admin_service(db)
    
    # Нельзя удалить самого себя
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    deleted = await admin_service.soft_delete_user(user_id, current_user.user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully", "user_id": user_id}


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
    
    restored = await admin_service.restore_user(user_id)
    if not restored:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or not deleted"
        )
    
    return {"message": "User restored successfully", "user_id": user_id}


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
    
    return await admin_service.block_user(
        user_id=user_id,
        block_data=block_data,
        admin_id=current_user.user_id
    )


@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Разблокировка пользователя
    """
    admin_service = await get_admin_service(db)
    
    unblocked = await admin_service.unblock_user(user_id)
    if not unblocked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User unblocked successfully", "user_id": user_id}


# ========== Управление ролями ==========

@router.post("/users/{user_id}/roles")
async def assign_role(
    user_id: int,
    role_data: dict,  # {"role_id": int}
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Назначение роли пользователю
    """
    admin_service = await get_admin_service(db)
    
    role_id = role_data.get("role_id")
    if not role_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="role_id required"
        )
    
    success = await admin_service.assign_role(user_id, role_id)
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
    
    # Получаем пользователя из БД для доступа к ролям
    from app.repositories.user_repo import UserRepository
    user_repo = UserRepository(db)
    user_model = await user_repo.get_by_id(user_id)
    
    if not user_model:
        return []
    
    roles = await user_model.awaitable_attrs.roles
    return [
        {
            "role_id": r.role_id,
            "role_title": r.role_title,
            "role_title_ru": r.role_title_ru,
            "role_code": r.role_code
        }
        for r in roles
    ]


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
    
    history = await admin_service.login_history_repo.get_by_user(user_id, limit)
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
    return await admin_service.get_stats()
