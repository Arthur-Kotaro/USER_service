# app/repositories/user_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, update
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _base_query(self):
        return select(User).options(
            selectinload(User.roles),
            selectinload(User.department),
        )

    async def get_by_id(self, user_id: int, include_deleted: bool = False) -> Optional[User]:
        query = self._base_query().where(User.user_id == user_id)
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_by_email(self, email: str, include_deleted: bool = False) -> Optional[User]:
        query = self._base_query().where(User.email == email)
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_by_username(self, username: str, include_deleted: bool = False) -> Optional[User]:
        query = self._base_query().where(User.user_name == username)
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        only_active: bool = True,
    ) -> List[User]:
        query = self._base_query()

        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))

        if only_active:
            query = query.where(
                or_(
                    User.blocked_at.is_(None),
                    and_(
                        User.block_expires_at.is_not(None),
                        User.block_expires_at <= datetime.now(timezone.utc),
                    ),
                )
            )

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.unique().scalars().all()

    async def create(
        self,
        email: str,
        username: str,
        hashed_password: str,
        position_id: int,
        last_name: str,
        first_name: str,
        middle_name: Optional[str] = None,
        dept_id=None,
        created_by: Optional[int] = None,
        **kwargs,
    ) -> User:
        user = User(
            email=email,
            user_name=username,
            password_hash=hashed_password,
            position_id=position_id,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            dept_id=dept_id,
            created_by=created_by,
            **kwargs,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        user = await self.get_by_id(user_id, include_deleted=True)
        if not user:
            return None

        forbidden_fields = {
            "user_id", "created_at", "password_hash", "deleted_at",
            "blocked_at", "blocked_by", "locked_until",
            "failed_login_attempts", "is_super_admin",
        }
        for key, value in update_data.items():
            if hasattr(user, key) and key not in forbidden_fields:
                setattr(user, key, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: int, soft: bool = True) -> bool:
        user = await self.get_by_id(user_id, include_deleted=True)
        if not user:
            return False
        if soft:
            user.deleted_at = datetime.now(timezone.utc)
            await self.db.commit()
        else:
            await self.db.delete(user)
            await self.db.commit()
        return True

    async def restore(self, user_id: int) -> bool:
        user = await self.get_by_id(user_id, include_deleted=True)
        if not user or user.deleted_at is None:
            return False
        user.deleted_at = None
        await self.db.commit()
        return True

    # ========== Блокировка ==========

    async def block_user(self, user_id: int, reason: str, blocked_by: int, expires_at=None) -> bool:
        user = await self.get_by_id(user_id, include_deleted=True)
        if not user or user.deleted_at is not None:
            return False
        user.blocked_at = datetime.now(timezone.utc)
        user.blocked_reason = reason
        user.blocked_by = blocked_by
        user.block_expires_at = expires_at
        await self.db.commit()
        return True

    async def unblock_user(self, user_id: int) -> bool:
        user = await self.get_by_id(user_id, include_deleted=True)
        if not user:
            return False
        user.blocked_at = None
        user.blocked_reason = None
        user.blocked_by = None
        user.block_expires_at = None
        await self.db.commit()
        return True

    # ========== Пароли ==========

    async def update_last_login(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def update_password(self, user_id: int, new_password_hash: str) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        user.password_hash = new_password_hash
        user.password_updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)
        return True

    async def set_temp_password(self, user_id: int, temp_password_hash: str, expires_at) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        user.temp_password = temp_password_hash
        user.temp_password_expires_at = expires_at
        await self.db.commit()
        return True

    async def clear_temp_password(self, user_id: int) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        user.temp_password = None
        user.temp_password_expires_at = None
        await self.db.commit()
        return True

    # ========== Фильтры ==========

    async def get_blocked_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.db.execute(
            select(User).where(
                User.blocked_at.is_not(None),
                User.deleted_at.is_(None),
            ).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_deleted_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.db.execute(
            select(User).where(User.deleted_at.is_not(None)).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_dept(self, dept_id) -> List[User]:
        result = await self.db.execute(
            self._base_query().where(
                User.dept_id == dept_id,
                User.deleted_at.is_(None),
            )
        )
        return result.unique().scalars().all()

    async def revoke_all_refresh_tokens(self, user_id: int) -> int:
        from app.models.refresh_token import RefreshToken
        result = await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
            .values(revoked=True)
        )
        await self.db.commit()
        return result.rowcount
