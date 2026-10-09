# app/api/v1/hr.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, user_to_response
from app.services.user_service import UserService
from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.department_repo import DepartmentRepository
from app.repositories.position_repo import PositionRepository
from app.utils.hasher import hash_password

router = APIRouter(tags=["HR"])


async def check_hr_or_admin(current_user: User):
    if current_user.is_super_admin:
        return True
    codes = current_user.get_role_codes()
    if "hr" in codes or "admin" in codes:
        return True
    raise HTTPException(status_code=403, detail="HR or admin privileges required")


def _make_service(db) -> UserService:
    return UserService(
        UserRepository(db),
        RoleRepository(db),
        DepartmentRepository(db),
        PositionRepository(db),
    )


@router.get("/departments")
async def get_departments(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    await check_hr_or_admin(current_user)
    repo = DepartmentRepository(db)
    deps = await repo.get_all()
    return [
        {
            "dept_id": str(d.dept_id),
            "dept_code": d.dept_code,
            "dept_name_en": d.dept_name_en,
            "dept_name_ru": d.dept_name_ru,
            "parent_dept_id": str(d.parent_dept_id) if d.parent_dept_id else None,
            "type": d.type,
            "level": d.level,
        }
        for d in deps
    ]


@router.get("/positions")
async def get_positions(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    await check_hr_or_admin(current_user)
    repo = PositionRepository(db)
    positions = await repo.get_all()
    return [
        {
            "position_id": p.position_id,
            "position_code": p.position_code,
            "position_name_en": p.position_name_en,
            "position_name_ru": p.position_name_ru,
        }
        for p in positions
    ]


@router.get("/roles")
async def get_roles(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    await check_hr_or_admin(current_user)
    repo = RoleRepository(db)
    roles = await repo.get_all()
    return [
        {
            "role_id": r.role_id,
            "role_code": r.role_code,
            "role_name_en": r.role_name_en,
            "role_name_ru": r.role_name_ru,
        }
        for r in roles
    ]


@router.get("/users/search", response_model=List[UserResponse])
async def search_users(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    await check_hr_or_admin(current_user)
    pattern = f"%{query}%"
    stmt = (
        select(User)
        .options(selectinload(User.roles), selectinload(User.department), selectinload(User.position))
        .where(
            User.deleted_at.is_(None),
            or_(
                User.last_name.ilike(pattern),
                User.first_name.ilike(pattern),
                User.user_name.ilike(pattern),
                User.email.ilike(pattern),
            ),
        )
        .limit(limit)
    )
    result = await db.execute(stmt)
    users = result.unique().scalars().all()
    return [user_to_response(u) for u in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    await check_hr_or_admin(current_user)
    service = _make_service(db)
    user = await service.get_user_by_id(user_id, include_deleted=True)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    await check_hr_or_admin(current_user)
    service = _make_service(db)
    password_hash = hash_password(user_data.password)
    return await service.create_user(
        user_data=user_data,
        password_hash=password_hash,
        created_by=current_user.user_id,
    )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    await check_hr_or_admin(current_user)
    service = _make_service(db)
    user = await service.get_user_by_id(user_id, include_deleted=True)
    if not user:
        raise HTTPException(404, "User not found")
    updated = await service.update_user(user_id, update_data.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(400, "Failed to update user")
    return updated


@router.post("/users/{user_id}/roles")
async def assign_role(
    user_id: int,
    role_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    await check_hr_or_admin(current_user)
    service = _make_service(db)
    if not await service.assign_role(user_id, role_id):
        raise HTTPException(400, "Failed to assign role")
    return {"message": "Role assigned successfully"}


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    await check_hr_or_admin(current_user)
    service = _make_service(db)
    if not await service.remove_role(user_id, role_id):
        raise HTTPException(400, "Failed to remove role")
    return {"message": "Role removed successfully"}


@router.post("/users/{user_id}/block")
async def block_user(
    user_id: int,
    reason: str = Query("Blocked by HR"),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    await check_hr_or_admin(current_user)
    service = _make_service(db)
    user = await service.get_user_by_id(user_id, include_deleted=True)
    if not user:
        raise HTTPException(404, "User not found")
    if user.is_super_admin:
        raise HTTPException(403, "Cannot block super admin")
    if not await service.block_user(user_id, reason, current_user.user_id):
        raise HTTPException(400, "Failed to block user")
    return {"message": "User blocked successfully"}


@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    await check_hr_or_admin(current_user)
    service = _make_service(db)
    if not await service.unblock_user(user_id):
        raise HTTPException(400, "Failed to unblock user")
    return {"message": "User unblocked successfully"}
