# app/repositories/user_repo.py (ОБНОВЛЁННАЯ ВЕРСИЯ)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ========== Базовые CRUD методы ==========
    
    async def get_by_id(self, user_id: int, include_deleted: bool = False) -> Optional[User]:
        """
        Получение пользователя по ID
        include_deleted: включать ли мягко удалённых пользователей
        """
        query = select(User).options(
            selectinload(User.roles), 
            selectinload(User.projects)
        ).where(User.user_id == user_id)
        
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()
    
    async def get_by_email(self, email: str, include_deleted: bool = False) -> Optional[User]:
        """
        Получение пользователя по email
        include_deleted: включать ли мягко удалённых пользователей
        """
        query = select(User).options(
            selectinload(User.roles), 
            selectinload(User.projects)
        ).where(User.email == email)
        
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()
    
    async def get_by_username(self, username: str, include_deleted: bool = False) -> Optional[User]:
        """
        Получение пользователя по имени пользователя
        include_deleted: включать ли мягко удалённых пользователей
        """
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
        """
        Получение списка пользователей
        include_deleted: включать ли мягко удалённых
        only_active: только активные (не заблокированные)
        """
        query = select(User)
        
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        
        if only_active:
            # Активный = не заблокирован (блокировка не истекла или её нет)
            query = query.where(
                or_(
                    User.blocked_at.is_(None),
                    and_(
                        User.block_expires_at.is_not(None),
                        User.block_expires_at <= datetime.now(timezone.utc)
                    )
                )
            )
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
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
    
    async def create(
        self, 
        email: str, 
        username: str, 
        hashed_password: str,
        **kwargs
    ) -> User:
        """
        Создание пользователя
        (status удалён - пользователь создаётся активным)
        """
        user = User(
            email=email,
            user_name=username,
            password_hash=hashed_password,
            # blocked_at, blocked_reason, blocked_by, block_expires_at остаются NULL
            # deleted_at остаётся NULL
            **kwargs
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update(self, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        """
        Обновление пользователя
        (status удалён из обновления)
        """
        user = await self.get_by_id(user_id, include_deleted=True)
        if not user:
            return None
        
        # Запрещаем обновление некоторых полей через этот метод
        forbidden_fields = ['user_id', 'created_at', 'password_hash', 'deleted_at', 'blocked_at']
        for key, value in update_data.items():
            if hasattr(user, key) and value is not None and key not in forbidden_fields:
                setattr(user, key, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def delete(self, user_id: int, soft: bool = True) -> bool:
        """
        Удаление пользователя
        soft: True - мягкое удаление (установка deleted_at)
              False - физическое удаление из БД
        """
        user = await self.get_by_id(user_id, include_deleted=True)
        if not user:
            return False
        
        if soft:
            # Мягкое удаление
            user.deleted_at = datetime.now(timezone.utc)
            await self.db.commit()
        else:
            # Физическое удаление
            await self.db.delete(user)
            await self.db.commit()
        
        return True
# Добавьте этот метод в класс UserRepository, если его нет

    async def unblock_user(self, user_id: int) -> bool:
        """
        Разблокировка пользователя
        """
        user = await self.get_by_id(user_id, include_deleted=True)
        if not user:
            return False
    
        user.blocked_at = None
        user.blocked_reason = None
        user.blocked_by = None
        user.block_expires_at = None
    
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
        """
        Блокировка пользователя
        """
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
        """
        Разблокировка пользователя
        """
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
        """
        Проверка, заблокирован ли пользователь
        (учитывает истечение временной блокировки)
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        if user.blocked_at is None:
            return False
        
        # Если временная блокировка истекла - считаем не заблокированным
        if user.block_expires_at is not None:
            if user.block_expires_at <= datetime.now(timezone.utc):
                return False
        
        return True
    
    async def auto_unblock_expired(self) -> int:
        """
        Автоматическая разблокировка пользователей с истекшей временной блокировкой
        Возвращает количество разблокированных пользователей
        """
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
