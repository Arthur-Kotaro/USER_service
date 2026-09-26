# app/api/v1/hr.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.role import Role
from app.models.department import Department
from app.schemas.user import UserCreate, UserUpdate, user_to_response
from app.schemas.admin import UserAdminResponse, user_to_admin_response
from app.services.user_service import UserService
from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.utils.hasher import hash_password

router = APIRouter(tags=["HR"])

async def check_hr_or_admin(current_user: User):
    """Проверка, что пользователь имеет роль hr или admin"""
    if current_user.is_super_admin:
        return True
    
    roles = current_user.get_roles_titles()
    if "hr" in roles or "admin" in roles:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="HR or admin privileges required"
    )

# ========== Departments ==========

@router.get("/departments")
async def get_departments(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Получение списка всех отделов (для HR и admin)"""
    await check_hr_or_admin(current_user)
    
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
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Получение списка всех ролей (для HR и admin)"""
    await check_hr_or_admin(current_user)
    
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

# ========== Users ==========

@router.get("/users/search")
async def search_users(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Поиск пользователей по ФИО, логину или email (только HR или admin)"""
    await check_hr_or_admin(current_user)
    
    search_pattern = f"%{query}%"
    stmt = select(User).options(
        selectinload(User.roles),
        selectinload(User.department)
    ).where(
        User.deleted_at.is_(None),
        or_(
            User.full_name.ilike(search_pattern),
            User.user_name.ilike(search_pattern),
            User.email.ilike(search_pattern)
        )
    ).limit(limit)
    
    result = await db.execute(stmt)
    users = result.unique().scalars().all()
    
    return [user_to_admin_response(u, u.get_roles_titles()) for u in users]

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Получение полной информации о пользователе (только HR или admin)"""
    await check_hr_or_admin(current_user)
    
    stmt = select(User).options(
        selectinload(User.roles),
        selectinload(User.department)
    ).where(User.user_id == user_id)
    
    result = await db.execute(stmt)
    user = result.unique().scalar_one_or_none()
    
    if not user:
        raise HTTPException(404, "User not found")
    
    return user_to_admin_response(user, user.get_roles_titles())

@router.post("/users")
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Создание нового пользователя (только HR или admin)"""
    await check_hr_or_admin(current_user)
    
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    user_service = UserService(user_repo, role_repo)
    
    existing = await user_repo.get_by_email(user_data.email)
    if existing:
        raise HTTPException(400, "User with this email already exists")
    
    existing = await user_repo.get_by_username(user_data.user_name)
    if existing:
        raise HTTPException(400, "User with this username already exists")
    
    hashed_password = hash_password(user_data.password)
    
    user = await user_service.create_user(
        email=user_data.email,
        username=user_data.user_name,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        gender=user_data.gender,
        birth_date=user_data.birth_date,
        dept_code=user_data.dept_code,
        phone_work=user_data.phone_work,
        phone_mobile=user_data.phone_mobile,
        head_id=user_data.head_id,
        role_ids=user_data.role_ids
    )
    
    return user

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Обновление информации о пользователе (только HR или admin)"""
    await check_hr_or_admin(current_user)
    
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    user_service = UserService(user_repo, role_repo)
    
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    updated_user = await user_service.update_user(user_id, update_dict)
    
    return updated_user

@router.post("/users/{user_id}/roles")
async def assign_role(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Назначение роли пользователю (только HR или admin)"""
    await check_hr_or_admin(current_user)
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    success = await user_repo.assign_role(user_id, role_id)
    if not success:
        raise HTTPException(400, "Failed to assign role")
    
    return {"message": "Role assigned successfully"}

@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Удаление роли у пользователя (только HR или admin)"""
    await check_hr_or_admin(current_user)
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    success = await user_repo.remove_role(user_id, role_id)
    if not success:
        raise HTTPException(400, "Failed to remove role")
    
    return {"message": "Role removed successfully"}

@router.post("/users/{user_id}/block")
async def block_user(
    user_id: int,
    reason: str = "Blocked by HR",
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Блокировка пользователя (только HR или admin)"""
    await check_hr_or_admin(current_user)
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    if user.is_super_admin:
        raise HTTPException(403, "Cannot block super admin")
    
    success = await user_repo.block_user(user_id, reason, current_user.user_id)
    if not success:
        raise HTTPException(400, "Failed to block user")
    
    return {"message": "User blocked successfully"}

@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Разблокировка пользователя (только HR или admin)"""
    await check_hr_or_admin(current_user)
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id, include_deleted=True)
    if not user:
        raise HTTPException(404, "User not found")
    
    success = await user_repo.unblock_user(user_id)
    if not success:
        raise HTTPException(400, "Failed to unblock user")
    
    return {"message": "User unblocked successfully"}
