# app/services/admin_service.py
from typing import List, Optional
from fastapi import HTTPException
from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.login_history_repo import LoginHistoryRepository
from app.schemas.user import UserAdminUpdate
from app.schemas.admin import UserAdminResponse, UserListResponse, user_to_admin_response
from app.utils.hasher import hash_password
from app.services.event_publisher import publish_user_event


class AdminService:
    def __init__(self, user_repo, role_repo, login_history_repo):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.login_history_repo = login_history_repo

    async def get_users(self, skip=0, limit=100, include_deleted=False, only_active=True) -> UserListResponse:
        users = await self.user_repo.get_all(skip, limit, include_deleted, only_active)
        return UserListResponse(
            total=len(users),
            users=[user_to_admin_response(u) for u in users],
        )

    async def get_user_by_id(self, user_id: int) -> Optional[UserAdminResponse]:
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            return None
        return user_to_admin_response(user)

    async def update_user_by_admin(self, user_id, update_data: UserAdminUpdate, admin_id) -> Optional[UserAdminResponse]:
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            return None
        if user.is_super_admin:
            admin = await self.user_repo.get_by_id(admin_id)
            if admin and not admin.is_super_admin:
                raise HTTPException(403, "Cannot modify super admin")
        update_dict = update_data.model_dump(exclude_unset=True)
        updated = await self.user_repo.update(user_id, update_dict)
        if not updated:
            return None
        return user_to_admin_response(updated)

    async def block_user(self, user_id, reason, admin_id):
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            raise HTTPException(404, "User not found")
        if user.deleted_at is not None:
            raise HTTPException(400, "User is already deleted")
        if user.is_super_admin:
            admin = await self.user_repo.get_by_id(admin_id)
            if admin and not admin.is_super_admin:
                raise HTTPException(403, "Cannot block super admin")
        ok = await self.user_repo.block_user(user_id, reason, admin_id)
        if not ok:
            raise HTTPException(400, "Failed to block user")
        await publish_user_event("user.blocked", user_id, {"reason": reason})
        return {"message": "User blocked successfully", "user_id": user_id}

    async def unblock_user(self, user_id: int) -> bool:
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            return False
        return await self.user_repo.unblock_user(user_id)

    async def soft_delete_user(self, user_id, admin_id) -> bool:
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            return False
        if user.is_super_admin:
            admin = await self.user_repo.get_by_id(admin_id)
            if admin and not admin.is_super_admin:
                raise HTTPException(403, "Cannot delete super admin")
        ok = await self.user_repo.delete(user_id, soft=True)
        if ok:
            await publish_user_event("user.deleted", user_id, {"by": admin_id})
        return ok

    async def restore_user(self, user_id: int) -> bool:
        return await self.user_repo.restore(user_id)

    async def get_deleted_users(self, skip=0, limit=100) -> List[dict]:
        users = await self.user_repo.get_deleted_users(skip, limit)
        return [
            {
                "user_id": u.user_id,
                "user_name": u.user_name,
                "email": u.email,
                "full_name": u.full_name,
                "deleted_at": u.deleted_at,
            }
            for u in users
        ]

    async def get_stats(self) -> dict:
        all_users = await self.user_repo.get_all(0, 10000, include_deleted=True)
        total = len(all_users)
        active = sum(1 for u in all_users if u.deleted_at is None and u.blocked_at is None)
        blocked = sum(1 for u in all_users if u.blocked_at is not None)
        deleted = sum(1 for u in all_users if u.deleted_at is not None)
        sa = sum(1 for u in all_users if u.is_super_admin and u.deleted_at is None)
        admins = sum(1 for u in all_users if not u.is_super_admin and u.has_role("admin") and u.deleted_at is None)
        regular = total - sa - admins - deleted
        return {
            "total_users": total,
            "active_users": active,
            "blocked_users": blocked,
            "deleted_users": deleted,
            "super_admin_users": sa,
            "admin_users": admins,
            "regular_users": regular,
        }

    async def assign_role(self, user_id, role_id) -> bool:
        return await self.role_repo.assign_role_to_user(user_id, role_id)

    async def remove_role(self, user_id, role_id) -> bool:
        return await self.role_repo.remove_role_from_user(user_id, role_id)

    async def reset_user_password(self, user_id, new_password) -> bool:
        user = await self.user_repo.get_by_id(user_id)
        if not user or user.deleted_at is not None:
            return False
        if len(new_password) < 12:
            raise HTTPException(400, "Password must be at least 12 characters")
        hashed = hash_password(new_password)
        updated = await self.user_repo.update_password(user_id, hashed)
        if updated:
            await self.user_repo.revoke_all_refresh_tokens(user_id)
        return updated
