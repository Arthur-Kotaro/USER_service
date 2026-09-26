# app/api/v1/admin.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.dependencies import get_current_user, get_current_admin
from app.models.user import User
from app.models.role import Role
from app.models.department import Department
from app.schemas.user import UserResponse, UserCreate, UserUpdate
from app.schemas.admin import (
    UserAdminResponse, user_to_admin_response,
    BlockUserRequest, UnblockUserRequest,
    AdminStatsResponse, BlockHistoryResponse,
    UserAdminUpdate
)
from app.services.user_service import UserService
from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.login_history_repo import LoginHistoryRepository
from app.utils.hasher import hash_password

router = APIRouter(tags=["Admin"])

# ========== Departments ==========

@router.get("/departments")
async def get_departments(
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """Получение списка всех отделов"""
    stmt = select(Department).order_by(Department.dept_code)
    result = await db.execute(stmt)
    departments = result.scalars().all()
    
    return [
        {
            "dept_code": d.dept_code,
            "dept_name": d.dept_name,
            "parent_dept_code": d.parent_dept_code
        }
        for d in departments
    ]

# ========== Roles ==========

@router.get("/roles")
async def get_roles(
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """Получение списка всех ролей"""
    stmt = select(Role).order_by(Role.role_id)
    result = await db.execute(stmt)
    roles = result.scalars().all()
    
    return [
        {
            "role_id": r.role_id,
            "role_title": r.role_title,
            "role_title_ru": r.role_title_ru,
            "role_code": r.role_code
        }
        for r in roles
    ]
