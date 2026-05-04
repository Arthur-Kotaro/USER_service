from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timezone
from app.models.user import User

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles), selectinload(User.projects))
            .where(User.user_id == user_id)
        )
        return result.unique().scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles), selectinload(User.projects))
            .where(User.email == email)
        )
        return result.unique().scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles), selectinload(User.projects))
            .where(User.user_name == username)
        )
        return result.unique().scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()
    
    async def create(self, email: str, username: str, hashed_password: str) -> User:
        user = User(
            email=email,
            user_name=username,
            password_hash=hashed_password,
            status="active"
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update(self, user_id: int, update_data: dict) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        for key, value in update_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def delete(self, user_id: int) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        await self.db.delete(user)
        await self.db.commit()
        return True
    
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
