# app/repositories/user_repo.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_, and_, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== Базовые CRUD методы ==========

    async def get_by_id(self, user_id: int, include_deleted: bool = False) -> Optional[User]:
        """Получение пользователя по ID"""
        query = select(User).options(
            selectinload(User.roles),
            selectinload(User.projects)
        ).where(User.user_id == user_id)

        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))

        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_by_email(self, email: str, include_deleted: bool = False) -> Optional[User]:
        """Получение пользователя по email"""
        query = select(User).options(
            selectinload(User.roles),
            selectinload(User.projects)
        ).where(User.email == email)

        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))

        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_by_username(self, username: str, include_deleted: bool = False) -> Optional[User]:
        """Получение пользователя по имени пользователя"""
        query = select(User).options(
            selectinload(User.roles),
            selectinload(User.projects)
        ).where(User.user_name == username)

        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))

        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        only_active: bool = True
    ) -> List[User]:
        """Получение списка пользователей"""
        query = select(User).options(
            selectinload(User.roles),
            selectinload(User.projects)
        )

        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))

        if only_active:
            query = query.where(
                or_(
                    User.blocked_at.is_(None),
                    and_(
                        User.block_expires_at.is_not(None),
                        User.block_expires_at <= datetime.now(timezone.utc)
                    )
                )
            )
            # НОВОЕ: Проверка временной блокировки (locked_until)
            query = query.where(
                or_(
                    User.locked_until.is_(None),
                    User.locked_until <= datetime.now(timezone.utc)
                )
            )

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.unique().scalars().all()

    async def get_blocked_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Получение списка заблокированных пользователей"""
        query = select(User).where(
            User.blocked_at.is_not(None),
            User.deleted_at.is_(None)
        ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_deleted_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Получение списка мягко удалённых пользователей"""
        query = select(User).where(
            User.deleted_at.is_not(None)
        ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_locked_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """НОВОЕ: Получение списка временно заблокированных пользователей"""
        now = datetime.now(timezone.utc)
        query = select(User).where(
            User.locked_until.is_not(None),
            User.locked_until > now,
            User.deleted_at.is_(None)
        ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(
        self,
        email: str,
        username: str,
        hashed_password: str,
        **kwargs
    ) -> User:
        """Создание пользователя"""
        user = User(
            email=email,
            user_name=username,
            password_hash=hashed_password,
            **kwargs
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        """Обновление пользователя"""
        user = await self.get_by_id(user_id, include_deleted=True)
        if not user:
            return None

        forbidden_fields = ['user_id', 'created_at', 'password_hash', 'deleted_at', 'blocked_at', 'locked_until', 'failed_login_attempts']
        for key, value in update_data.items():
            if hasattr(user, key) and value is not None and key not in forbidden_fields:
                setattr(user, key, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: int, soft: bool = True) -> bool:
        """Удаление пользователя"""
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
        """Восстановление мягко удалённого пользователя"""
        user = await self.get_by_id(user_id, include_deleted=True)
        if not user or user.deleted_at is None:
            return False

        user.deleted_at = None
        await self.db.commit()
        return True

    # ========== Методы для работы с блокировками ==========

    async def block_user(
        self,
        user_id: int,
        reason: str,
        blocked_by: int,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Блокировка пользователя"""
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
        """Разблокировка пользователя"""
        user = await self.get_by_id(user_id, include_deleted=True)
        if not user:
            return False

        user.blocked_at = None
        user.blocked_reason = None
        user.blocked_by = None
        user.block_expires_at = None

        await self.db.commit()
        return True

    async def is_user_blocked(self, user_id: int) -> bool:
        """Проверка, заблокирован ли пользователь"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        if user.blocked_at is None:
            return False

        if user.block_expires_at is not None:
            if user.block_expires_at <= datetime.now(timezone.utc):
                return False

        return True

    async def auto_unblock_expired(self) -> int:
        """Автоматическая разблокировка пользователей с истекшей временной блокировкой"""
        now = datetime.now(timezone.utc)
        query = select(User).where(
            User.blocked_at.is_not(None),
            User.block_expires_at.is_not(None),
            User.block_expires_at <= now,
            User.deleted_at.is_(None)
        )
        result = await self.db.execute(query)
        users = result.scalars().all()

        for user in users:
            user.blocked_at = None
            user.blocked_reason = None
            user.blocked_by = None
            user.block_expires_at = None

        await self.db.commit()
        return len(users)

    async def auto_unlock_locked(self) -> int:
        """НОВОЕ: Автоматическая разблокировка пользователей с истекшей временной блокировкой (locked_until)"""
        now = datetime.now(timezone.utc)
        query = select(User).where(
            User.locked_until.is_not(None),
            User.locked_until <= now,
            User.deleted_at.is_(None)
        )
        result = await self.db.execute(query)
        users = result.scalars().all()

        for user in users:
            user.locked_until = None
            user.failed_login_attempts = 0

        await self.db.commit()
        return len(users)

    # ========== Методы для работы с паролями ==========

    async def update_last_login(self, user_id: int) -> None:
        """Обновление времени последнего входа"""
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """Обновление пароля"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.password_hash = new_password_hash
        user.password_updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)
        return True

    async def set_temp_password(self, user_id: int, temp_password_hash: str, expires_at: datetime) -> bool:
        """Установка временного пароля"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.temp_password = temp_password_hash
        user.temp_password_expires_at = expires_at
        await self.db.commit()
        return True

    async def clear_temp_password(self, user_id: int) -> bool:
        """Очистка временного пароля"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.temp_password = None
        user.temp_password_expires_at = None
        await self.db.commit()
        return True

    # ========== Методы для работы с ролями ==========

    async def assign_role(self, user_id: int, role_id: int) -> bool:
        """Назначение роли пользователю"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        from app.models.role import Role
        result = await self.db.execute(select(Role).where(Role.role_id == role_id))
        role = result.scalar_one_or_none()

        if not role:
            return False

        if role not in user.roles:
            user.roles.append(role)
            await self.db.commit()

        return True

    async def remove_role(self, user_id: int, role_id: int) -> bool:
        """Удаление роли у пользователя"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        from app.models.role import Role
        result = await self.db.execute(select(Role).where(Role.role_id == role_id))
        role = result.scalar_one_or_none()

        if role and role in user.roles:
            user.roles.remove(role)
            await self.db.commit()

        return True

    async def get_user_roles(self, user_id: int) -> List[str]:
        """Получение списка ролей пользователя"""
        user = await self.get_by_id(user_id)
        if not user:
            return []
        return [role.role_title for role in user.roles]

    # ========== НОВОЕ: Методы для работы с иерархией ==========

    async def get_subordinates(self, user_id: int) -> List[User]:
        """Получить подчиненных пользователя"""
        result = await self.db.execute(
            select(User).where(
                User.head_id == user_id,
                User.deleted_at.is_(None)
            )
        )
        return result.scalars().all()

    async def get_team(self, user_id: int, include_head: bool = False) -> List[User]:
        """Получить команду пользователя (включая его самого)"""
        user = await self.get_by_id(user_id)
        if not user:
            return []

        result = await self.db.execute(
            select(User).where(
                or_(
                    User.head_id == user_id,
                    User.user_id == user_id if include_head else False
                ),
                User.deleted_at.is_(None)
            )
        )
        return result.scalars().all()
