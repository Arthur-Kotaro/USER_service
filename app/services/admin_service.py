# app/services/admin_service.py
from typing import List, Optional
from fastapi import HTTPException, status

from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.login_history_repo import LoginHistoryRepository
from app.schemas.admin import (
    UserAdminUpdate, UserAdminResponse, UserListResponse,
    BlockUserRequest, BlockUserResponse, DeletedUserResponse,
    AdminStatsResponse, user_to_admin_response,
)
from app.models.user import User
from app.utils.hasher import hash_password


class AdminService:
    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        login_history_repo: LoginHistoryRepository,
    ):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.login_history_repo = login_history_repo

    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        only_active: bool = True,
    ) -> UserListResponse:
        users = await self.user_repo.get_all(skip, limit, include_deleted, only_active)
        total = len(users)
        return UserListResponse(
            total=total,
            users=[user_to_admin_response(u, u.get_roles_titles()) for u in users],
        )

    async def get_user_by_id(self, user_id: int) -> Optional[UserAdminResponse]:
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            return None
        return user_to_admin_response(user, user.get_roles_titles())

    async def update_user_by_admin(
        self,
        user_id: int,
        update_data: UserAdminUpdate,
        admin_id: int,
    ) -> Optional[UserAdminResponse]:
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            return None

        if user.is_super_admin:
            admin = await self.user_repo.get_by_id(admin_id)
            if admin and not admin.is_super_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot modify super admin",
                )

        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict.pop("is_super_admin", None)

        updated = await self.user_repo.update(user_id, update_dict)
        if not updated:
            return None
        return user_to_admin_response(updated, updated.get_roles_titles())

    async def block_user(
        self,
        user_id: int,
        block_data: BlockUserRequest,
        admin_id: int,
    ) -> BlockUserResponse:
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.deleted_at is not None:
            raise HTTPException(status_code=400, detail="User is already deleted")

        if user.is_super_admin:
            admin = await self.user_repo.get_by_id(admin_id)
            if admin and not admin.is_super_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot block super admin",
                )

        blocked = await self.user_repo.block_user(
            user_id=user_id,
            reason=block_data.reason,
            blocked_by=admin_id,
            expires_at=block_data.expires_at,
        )
        if not blocked:
            raise HTTPException(status_code=400, detail="Failed to block user")

        user = await self.user_repo.get_by_id(user_id)
        admin = await self.user_repo.get_by_id(admin_id)

        return BlockUserResponse(
            user_id=user.user_id,
            user_name=user.user_name,
            blocked_at=user.blocked_at,
            blocked_reason=user.blocked_reason,
            block_expires_at=user.block_expires_at,
            blocked_by=admin_id,
            blocked_by_name=admin.user_name if admin else None,
        )

    async def unblock_user(self, user_id: int) -> bool:
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            return False
        return await self.user_repo.unblock_user(user_id)

    async def soft_delete_user(self, user_id: int, admin_id: int) -> bool:
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            return False

        if user.is_super_admin:
            admin = await self.user_repo.get_by_id(admin_id)
            if admin and not admin.is_super_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot delete super admin",
                )

        return await self.user_repo.delete(user_id, soft=True)

    async def restore_user(self, user_id: int) -> bool:
        return await self.user_repo.restore(user_id)

    async def get_deleted_users(
        self, skip: int = 0, limit: int = 100
    ) -> List[DeletedUserResponse]:
        users = await self.user_repo.get_deleted_users(skip, limit)
        return [
            DeletedUserResponse(
                user_id=u.user_id,
                user_name=u.user_name,
                email=u.email,
                deleted_at=u.deleted_at,
                deleted_reason=None,
                deleted_by=None,
                deleted_by_name=None,
            )
            for u in users
        ]

    async def get_stats(self) -> AdminStatsResponse:
        all_users = await self.user_repo.get_all(0, 10000, include_deleted=True)

        total = len(all_users)
        active = sum(1 for u in all_users if u.deleted_at is None and u.blocked_at is None)
        blocked = sum(1 for u in all_users if u.blocked_at is not None)
        deleted = sum(1 for u in all_users if u.deleted_at is not None)

        admin_count = 0
        super_admin_count = 0
        regular_count = 0

        for u in all_users:
            if u.deleted_at is not None:
                continue
            if u.is_super_admin:
                super_admin_count += 1
            elif u.has_role("admin"):
                admin_count += 1
            else:
                regular_count += 1

        return AdminStatsResponse(
            total_users=total,
            active_users=active,
            blocked_users=blocked,
            locked_users=0,
            deleted_users=deleted,
            admin_users=admin_count,
            super_admin_users=super_admin_count,
            regular_users=regular_count,
            users_with_temp_password=0,
            users_password_expiring_soon=0,
        )

    async def assign_role(self, user_id: int, role_id: int) -> bool:
        return await self.role_repo.assign_role_to_user(user_id, role_id)

    async def remove_role(self, user_id: int, role_id: int) -> bool:
        return await self.role_repo.remove_role_from_user(user_id, role_id)

    async def reset_user_password(self, user_id: int, new_password: str) -> bool:
        user = await self.user_repo.get_by_id(user_id)
        if not user or user.deleted_at is not None:
            return False

        if len(new_password) < 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 12 characters",
            )

        hashed = hash_password(new_password)
        updated = await self.user_repo.update_password(user_id, hashed)

        if updated:
            await self.user_repo.revoke_all_refresh_tokens(user_id)

        return updated
