# app/repositories/role_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from typing import Optional, List
from app.models.role import Role, users_roles


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, role_id: int) -> Optional[Role]:
        result = await self.db.execute(
            select(Role).where(Role.role_id == role_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, role_code: str) -> Optional[Role]:
        result = await self.db.execute(
            select(Role).where(Role.role_code == role_code)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Role]:
        result = await self.db.execute(
            select(Role).order_by(Role.role_code).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(
        self,
        role_code: str,
        role_name_en: str,
        role_name_ru: str,
    ) -> Role:
        role = Role(
            role_code=role_code,
            role_name_en=role_name_en,
            role_name_ru=role_name_ru,
        )
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def update(self, role_id: int, **kwargs) -> Optional[Role]:
        role = await self.get_by_id(role_id)
        if not role:
            return None
        for key, value in kwargs.items():
            if hasattr(role, key) and value is not None:
                setattr(role, key, value)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def delete(self, role_id: int) -> bool:
        role = await self.get_by_id(role_id)
        if not role:
            return False
        await self.db.delete(role)
        await self.db.commit()
        return True

    async def get_user_roles(self, user_id: int) -> List[Role]:
        result = await self.db.execute(
            select(Role).join(users_roles).where(users_roles.c.user_id == user_id)
        )
        return result.scalars().all()

    async def assign_role_to_user(self, user_id: int, role_id: int) -> bool:
        result = await self.db.execute(
            select(users_roles).where(
                users_roles.c.user_id == user_id,
                users_roles.c.role_id == role_id,
            )
        )
        if result.first():
            return False
        await self.db.execute(
            insert(users_roles).values(user_id=user_id, role_id=role_id)
        )
        await self.db.commit()
        return True

    async def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        result = await self.db.execute(
            select(users_roles).where(
                users_roles.c.user_id == user_id,
                users_roles.c.role_id == role_id,
            )
        )
        if not result.first():
            return False
        await self.db.execute(
            delete(users_roles).where(
                users_roles.c.user_id == user_id,
                users_roles.c.role_id == role_id,
            )
        )
        await self.db.commit()
        return True

    async def set_user_roles(self, user_id: int, role_ids: List[int]) -> None:
        await self.db.execute(
            delete(users_roles).where(users_roles.c.user_id == user_id)
        )
        for role_id in role_ids:
            await self.db.execute(
                insert(users_roles).values(user_id=user_id, role_id=role_id)
            )
        await self.db.commit()
