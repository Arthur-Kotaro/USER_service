# app/services/user_service.py
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.department_repo import DepartmentRepository
from app.repositories.position_repo import PositionRepository
from app.schemas.user import UserResponse, UserCreate, user_to_response
from app.models.user import User


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        department_repo: Optional[DepartmentRepository] = None,
        position_repo: Optional[PositionRepository] = None,
    ):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.department_repo = department_repo
        self.position_repo = position_repo

    async def get_user_by_id(self, user_id: int, include_deleted: bool = False) -> Optional[UserResponse]:
        user = await self.user_repo.get_by_id(user_id, include_deleted=include_deleted)
        if not user:
            return None
        return user_to_response(user)

    async def get_user_by_email(self, email: str, include_deleted: bool = False) -> Optional[User]:
        return await self.user_repo.get_by_email(email, include_deleted=include_deleted)

    async def get_user_by_username(self, username: str, include_deleted: bool = False) -> Optional[User]:
        return await self.user_repo.get_by_username(username, include_deleted=include_deleted)

    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        only_active: bool = True,
    ) -> List[UserResponse]:
        users = await self.user_repo.get_all(skip, limit, include_deleted, only_active)
        return [user_to_response(u) for u in users]

    async def create_user(
        self,
        user_data: UserCreate,
        password_hash: str,
        created_by: Optional[int] = None,
    ) -> UserResponse:
        existing_email = await self.user_repo.get_by_email(user_data.email)
        if existing_email:
            raise HTTPException(status_code=400, detail="User with this email already exists")

        existing_username = await self.user_repo.get_by_username(user_data.user_name)
        if existing_username:
            raise HTTPException(status_code=400, detail="User with this username already exists")

        if self.position_repo:
            position = await self.position_repo.get_by_id(user_data.position_id)
            if not position:
                raise HTTPException(status_code=400, detail="Position not found")

        user = await self.user_repo.create(
            email=user_data.email,
            username=user_data.user_name,
            hashed_password=password_hash,
            position_id=user_data.position_id,
            last_name=user_data.last_name,
            first_name=user_data.first_name,
            middle_name=user_data.middle_name,
            dept_id=user_data.dept_id,
            created_by=created_by,
            gender=user_data.gender,
            birth_date=user_data.birth_date,
            phone_work=user_data.phone_work,
            phone_mobile=user_data.phone_mobile,
        )

        for role_id in (user_data.role_ids or []):
            await self.role_repo.assign_role_to_user(user.user_id, role_id)

        user = await self.user_repo.get_by_id(user.user_id)
        return user_to_response(user)

    async def update_user(self, user_id: int, update_data: Dict[str, Any]) -> Optional[UserResponse]:
        forbidden = {
            "user_id", "password_hash", "created_at", "deleted_at",
            "blocked_at", "locked_until", "failed_login_attempts",
            "is_super_admin", "created_by",
        }
        filtered_data = {k: v for k, v in update_data.items() if k not in forbidden}

        user = await self.user_repo.update(user_id, filtered_data)
        if not user:
            return None
        return user_to_response(user)

    async def delete_user(self, user_id: int, soft: bool = True) -> bool:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
        return await self.user_repo.delete(user_id, soft=soft)

    async def restore_user(self, user_id: int) -> Optional[UserResponse]:
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user or user.deleted_at is None:
            return None
        restored = await self.user_repo.restore(user_id)
        if not restored:
            return None
        user = await self.user_repo.get_by_id(user_id)
        return user_to_response(user)

    async def block_user(self, user_id: int, reason: str, blocked_by: int, expires_at=None) -> bool:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
        return await self.user_repo.block_user(user_id, reason, blocked_by, expires_at)

    async def unblock_user(self, user_id: int) -> bool:
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            return False
        return await self.user_repo.unblock_user(user_id)

    async def is_user_blocked(self, user_id: int) -> bool:
        user = await self.user_repo.get_by_id(user_id)
        if not user or user.blocked_at is None:
            return False
        from datetime import datetime, timezone
        if user.block_expires_at is not None:
            if user.block_expires_at <= datetime.now(timezone.utc):
                return False
        return True

    # ========== Роли ==========

    async def assign_role(self, user_id: int, role_id: int) -> bool:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
        return await self.role_repo.assign_role_to_user(user_id, role_id)

    async def assign_role_by_code(self, user_id: int, role_code: str) -> bool:
        role = await self.role_repo.get_by_code(role_code)
        if not role:
            return False
        return await self.assign_role(user_id, role.role_id)

    async def remove_role(self, user_id: int, role_id: int) -> bool:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
        return await self.role_repo.remove_role_from_user(user_id, role_id)

    async def get_user_roles(self, user_id: int) -> List[str]:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return []
        return user.get_role_codes()

    async def get_user_role_objects(self, user_id: int) -> List:
        return await self.role_repo.get_user_roles(user_id)

    # ========== Фильтры ==========

    async def get_users_by_dept(self, dept_id) -> List[UserResponse]:
        users = await self.user_repo.get_by_dept(dept_id)
        return [user_to_response(u) for u in users]

    async def get_blocked_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        users = await self.user_repo.get_blocked_users(skip, limit)
        return [user_to_response(u) for u in users]

    async def get_deleted_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        users = await self.user_repo.get_deleted_users(skip, limit)
        return [user_to_response(u) for u in users]
