# app/api/v1/admin.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.schemas.admin import (
    UserAdminUpdate,
    UserAdminResponse,
    UserListResponse,
    AdminStatsResponse
)
from app.services.admin_service import AdminService
from app.services.user_management_service import UserManagementService
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])

# ========== Управление пользователями ==========

@router.post("/users", response_model=UserAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserAdminUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Создание нового пользователя (только администратор)
    """
    admin_service = AdminService(db)
    
    # Проверка на существование
    existing = await admin_service.get_user_by_username(user_data.username)
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
    
    user = await admin_service.create_user(user_data)
    return user

@router.get("/users", response_model=UserListResponse)
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, pattern="^(active|blocked|archived)$"),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Получение списка пользователей с фильтрацией и пагинацией
    """
    admin_service = AdminService(db)
    
    users, total = await admin_service.get_all_users(
        skip=skip, 
        limit=limit, 
        status_filter=status_filter,
        search=search
    )
    
    return UserListResponse(
        total=total,
        users=users,
        skip=skip,
        limit=limit
    )

@router.get("/users/{user_id}", response_model=UserAdminResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Получение информации о пользователе по ID
    """
    admin_service = AdminService(db)
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
    db: Session = Depends(get_db)
):
    """
    Обновление данных пользователя
    """
    admin_service = AdminService(db)
    
    user = await admin_service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Удаление пользователя (мягкое удаление - архивация)
    """
    admin_service = AdminService(db)
    
    # Нельзя удалить самого себя
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    deleted = await admin_service.delete_user(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return None

# ========== Блокировка пользователей ==========

@router.post("/users/{user_id}/block")
async def block_user(
    user_id: int,
    block_data: dict,  # Временно заменим на dict, так как схема может не существовать
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Блокировка пользователя
    """
    admin_service = AdminService(db)
    
    # Нельзя заблокировать самого себя
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot block your own account"
        )
    
    user = await admin_service.block_user(
        user_id=user_id,
        admin_id=current_user.user_id,
        reason=block_data.get("reason"),
        expires_at=block_data.get("expires_at")
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
        "reason": block_data.get("reason")
    }

@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Разблокировка пользователя
    """
    admin_service = AdminService(db)
    
    user = await admin_service.unblock_user(user_id)
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
    role_data: dict,  # Временно заменим на dict
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Назначение роли пользователю
    """
    admin_service = AdminService(db)
    
    # Проверка существования пользователя
    user = await admin_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = await admin_service.assign_role(user_id, role_data.get("role_id"))
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
    db: Session = Depends(get_db)
):
    """
    Удаление роли у пользователя
    """
    admin_service = AdminService(db)
    
    success = await admin_service.remove_role(user_id, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove role"
        )
    
    return {"message": "Role removed successfully"}

# ========== Управление проектами ==========

@router.post("/users/{user_id}/projects")
async def assign_project(
    user_id: int,
    project_data: dict,  # Временно заменим на dict
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Назначение проекта пользователю
    """
    admin_service = AdminService(db)
    
    success = await admin_service.assign_project(user_id, project_data.get("project_id"))
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
    db: Session = Depends(get_db)
):
    """
    Удаление проекта у пользователя
    """
    admin_service = AdminService(db)
    
    success = await admin_service.remove_project(user_id, project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove project"
        )
    
    return {"message": "Project removed successfully"}

# ========== Статистика ==========

@router.get("/stats/overview", response_model=AdminStatsResponse)
async def get_admin_stats(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Получение статистики для администратора
    """
    admin_service = AdminService(db)
    stats = await admin_service.get_stats()
    return stats

@router.get("/stats/users/daily")
async def get_daily_registrations(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Получение статистики регистраций по дням
    """
    admin_service = AdminService(db)
    stats = await admin_service.get_daily_registrations(days)
    return stats
