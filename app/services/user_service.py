# app/services/user_service.py
from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserResponse
from app.models.user import User

class UserService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)
    
    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """Получить пользователя по ID"""
        user = await self.user_repo.get_by_id(user_id)
        if user:
            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                is_admin=user.is_admin,
                created_at=user.created_at
            )
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        return await self.user_repo.get_by_email(email)
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """Получить список всех пользователей"""
        users = await self.user_repo.get_all(skip, limit)
        return [
            UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                is_admin=user.is_admin,
                created_at=user.created_at
            )
            for user in users
        ]
    
    async def update_user(self, user_id: int, update_data: dict) -> Optional[UserResponse]:
        """Обновить данные пользователя"""
        user = await self.user_repo.update(user_id, update_data)
        if user:
            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                is_admin=user.is_admin,
                created_at=user.created_at
            )
        return None
    
    async def delete_user(self, user_id: int) -> bool:
        """Удалить пользователя"""
        return await self.user_repo.delete(user_id)
    
    async def activate_user(self, user_id: int) -> Optional[UserResponse]:
        """Активировать пользователя"""
        return await self.update_user(user_id, {"is_active": True})
    
    async def deactivate_user(self, user_id: int) -> Optional[UserResponse]:
        """Деактивировать пользователя"""
        return await self.update_user(user_id, {"is_active": False})
    
    async def make_admin(self, user_id: int) -> Optional[UserResponse]:
        """Сделать пользователя администратором"""
        return await self.update_user(user_id, {"is_admin": True})
    
    async def remove_admin(self, user_id: int) -> Optional[UserResponse]:
        """Убрать права администратора"""
        return await self.update_user(user_id, {"is_admin": False})
