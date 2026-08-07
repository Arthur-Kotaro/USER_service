# app/repositories/role_repo.py (НОВЫЙ ФАЙЛ)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional, List
from app.models.role import Role, users_roles


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, role_id: int) -> Optional[Role]:
        """Получение роли по ID"""
        result = await self.db.execute(
            select(Role).where(Role.role_id == role_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_title(self, title: str) -> Optional[Role]:
        """Получение роли по английскому названию"""
        result = await self.db.execute(
            select(Role).where(Role.role_title == title)
        )
        return result.scalar_one_or_none()
    
    async def get_by_code(self, code: str) -> Optional[Role]:
        """Получение роли по буквенному коду"""
        result = await self.db.execute(
            select(Role).where(Role.role_code == code)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Role]:
        """Получение всех ролей"""
        result = await self.db.execute(
            select(Role).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def create(
        self, 
        role_title: str, 
        role_title_ru: Optional[str] = None,
        role_code: Optional[str] = None
    ) -> Role:
        """Создание новой роли"""
        role = Role(
            role_title=role_title,
            role_title_ru=role_title_ru,
            role_code=role_code
        )
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def update(self, role_id: int, update_data: dict) -> Optional[Role]:
        """Обновление роли"""
        role = await self.get_by_id(role_id)
        if not role:
            return None
        
        for key, value in update_data.items():
            if hasattr(role, key) and value is not None:
                setattr(role, key, value)
        
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def delete(self, role_id: int) -> bool:
        """Удаление роли"""
        role = await self.get_by_id(role_id)
        if not role:
            return False
        
        await self.db.delete(role)
        await self.db.commit()
        return True
    
    async def get_user_roles(self, user_id: int) -> List[Role]:
        """Получение всех ролей пользователя"""
        result = await self.db.execute(
            select(Role).join(users_roles).where(users_roles.c.user_id == user_id)
        )
        return result.scalars().all()
    
    async def assign_role_to_user(self, user_id: int, role_id: int) -> bool:
        """Назначение роли пользователю"""
        # Проверяем, не назначена ли уже
        result = await self.db.execute(
            select(users_roles).where(
                users_roles.c.user_id == user_id,
                users_roles.c.role_id == role_id
            )
        )
        if result.first():
            return False
        
        # Назначаем роль
        await self.db.execute(
            users_roles.insert().values(user_id=user_id, role_id=role_id)
        )
        await self.db.commit()
        return True
    
    async def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        """Удаление роли у пользователя"""
        result = await self.db.execute(
            select(users_roles).where(
                users_roles.c.user_id == user_id,
                users_roles.c.role_id == role_id
            )
        )
        if not result.first():
            return False
        
        await self.db.execute(
            users_roles.delete().where(
                users_roles.c.user_id == user_id,
                users_roles.c.role_id == role_id
            )
        )
        await self.db.commit()
        return True
