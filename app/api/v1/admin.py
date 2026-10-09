# app/api/v1/admin.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from app.database import get_db
from app.dependencies import get_current_admin
from app.models.user import User
from app.schemas.user import UserAdminUpdate, UserResponse, user_to_response
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


@router.get("/users")
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


@router.get("/users/deleted")
async def get_deleted_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    return await service.get_deleted_users(skip, limit)


@router.get("/users/{user_id}", response_model=UserResponse)
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


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_by_admin(
    user_id: int,
    update_data: UserAdminUpdate,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    updated = await service.update_user_by_admin(user_id, update_data, current_user.user_id)
    if not updated:
        raise HTTPException(404, "User not found")
    return updated


@router.post("/users/{user_id}/block")
async def block_user(
    user_id: int,
    reason: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    return await service.block_user(user_id, reason, current_user.user_id)


@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    if not await service.unblock_user(user_id):
        raise HTTPException(404, "User not found")
    return {"message": "User unblocked successfully"}


@router.delete("/users/{user_id}")
async def soft_delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    if not await service.soft_delete_user(user_id, current_user.user_id):
        raise HTTPException(404, "User not found")
    return {"message": "User soft-deleted successfully"}


@router.post("/users/{user_id}/restore")
async def restore_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    if not await service.restore_user(user_id):
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
    if not await service.assign_role(user_id, role_id):
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
    if not await service.remove_role(user_id, role_id):
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
    if not await service.reset_user_password(user_id, new_password):
        raise HTTPException(404, "User not found or deleted")
    return {"message": "Password reset successfully"}


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_admin),
    db=Depends(get_db),
):
    service = _make_service(db)
    return await service.get_stats()
