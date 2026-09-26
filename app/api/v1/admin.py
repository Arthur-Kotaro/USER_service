# app/api/v1/admin.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.dependencies import get_current_admin
from app.models.user import User
from app.models.role import Role
from app.models.department import Department
from app.schemas.admin import (
    UserAdminResponse, UserAdminUpdate, UserListResponse,
    BlockUserRequest, BlockUserResponse,
    DeletedUserResponse, AdminStatsResponse,
)
from app.services.admin_service import AdminService
from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.login_history_repo import LoginHistoryRepository


router = APIRouter(tags=["Admin"])


def _make_service(db) -> AdminService:
    return AdminService(
        UserRepository(db),
        RoleRepository(db),
        LoginHistoryRepository(db),
    )


@router.get("/departments")
async def get_departments(
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    stmt = select(Department).order_by(Department.dept_code)
    result = await db.execute(stmt)
    departments = result.scalars().all()
    return [
        {
            "dept_code": d.dept_code,
            "dept_name": d.dept_name,
            "parent_dept_code": d.parent_dept_code,
        }
        for d in departments
    ]


@router.get("/roles")
async def get_roles(
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    stmt = select(Role).order_by(Role.role_id)
    result = await db.execute(stmt)
    roles = result.scalars().all()
    return [
        {
            "role_id": r.role_id,
            "role_title": r.role_title,
            "role_title_ru": r.role_title_ru,
            "role_code": r.role_code,
        }
        for r in roles
    ]


@router.get("/users", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    include_deleted: bool = Query(False),
    only_active: bool = Query(True),
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    return await service.get_users(skip, limit, include_deleted, only_active)


@router.get("/users/deleted", response_model=List[DeletedUserResponse])
async def get_deleted_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    return await service.get_deleted_users(skip, limit)


@router.get("/users/{user_id}", response_model=UserAdminResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.put("/users/{user_id}", response_model=UserAdminResponse)
async def update_user_by_admin(
    user_id: int,
    update_data: UserAdminUpdate,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    updated = await service.update_user_by_admin(
        user_id, update_data, current_user.user_id,
    )
    if not updated:
        raise HTTPException(404, "User not found")
    return updated


@router.post("/users/{user_id}/block", response_model=BlockUserResponse)
async def block_user(
    user_id: int,
    block_data: BlockUserRequest,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    return await service.block_user(user_id, block_data, current_user.user_id)


@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    success = await service.unblock_user(user_id)
    if not success:
        raise HTTPException(404, "User not found")
    return {"message": "User unblocked successfully"}


@router.delete("/users/{user_id}")
async def soft_delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    success = await service.soft_delete_user(user_id, current_user.user_id)
    if not success:
        raise HTTPException(404, "User not found")
    return {"message": "User soft-deleted successfully"}


@router.post("/users/{user_id}/restore")
async def restore_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    success = await service.restore_user(user_id)
    if not success:
        raise HTTPException(404, "User not found or not deleted")
    return {"message": "User restored successfully"}


@router.post("/users/{user_id}/roles")
async def assign_role(
    user_id: int,
    role_id: int = Query(...),
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    success = await service.assign_role(user_id, role_id)
    if not success:
        raise HTTPException(400, "Failed to assign role")
    return {"message": "Role assigned successfully"}


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    success = await service.remove_role(user_id, role_id)
    if not success:
        raise HTTPException(400, "Failed to remove role")
    return {"message": "Role removed successfully"}


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    new_password: str = Query(..., min_length=12),
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    success = await service.reset_user_password(user_id, new_password)
    if not success:
        raise HTTPException(404, "User not found or deleted")
    return {"message": "Password reset successfully"}


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    return await service.get_stats()
