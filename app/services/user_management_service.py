# app/services/user_management_service.py
from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories.user_repo import UserRepository
from app.models.user import User
from app.models.role import Role

class UserManagementService:
    """Сервис для управления пользователями (только для админов)"""
    
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)
    
    async def create_user(self, user_data: dict) -> User:
        """Создание пользователя админом"""
        # Проверка на существование
        if await self.user_repo.get_by_username(user_data["user_name"]):
            raise ValueError("Username already exists")
        
        if user_data.get("email") and await self.user_repo.get_by_email(user_data["email"]):
            raise ValueError("Email already exists")
        
        return await self.user_repo.create(**user_data)
    
    async def update_user(self, user_id: int, update_data: dict) -> Optional[User]:
        """Обновление пользователя админом"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        # Нельзя изменить user_name? Обычно нет
        if "user_name" in update_data:
            raise ValueError("Cannot change username")
        
        return await self.user_repo.update(user_id, update_data)
    
    async def block_user(self, user_id: int, admin_id: int, reason: str, expires_at=None) -> Optional[User]:
        """Блокировка пользователя"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        update_data = {
            "status": "blocked",
            "blocked_at": func.now(),
            "blocked_reason": reason,
            "blocked_by": admin_id,
            "block_expires_at": expires_at
        }
        return await self.user_repo.update(user_id, update_data)
    
    async def unblock_user(self, user_id: int) -> Optional[User]:
        """Разблокировка пользователя"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        update_data = {
            "status": "active",
            "blocked_at": None,
            "blocked_reason": None,
            "blocked_by": None,
            "block_expires_at": None
        }
        return await self.user_repo.update(user_id, update_data)
    
    async def archive_user(self, user_id: int) -> Optional[User]:
        """Архивация пользователя"""
        return await self.user_repo.update(user_id, {"status": "archived"})
    
    async def assign_role(self, user_id: int, role_id: int) -> bool:
        """Назначение роли пользователю"""
        # Используйте прямые SQL-запросы для связи многие-ко-многим
        from sqlalchemy import text
        result = await self.user_repo.db.execute(
            text("INSERT INTO users_roles (user_id, role_id) VALUES (:user_id, :role_id)"),
            {"user_id": user_id, "role_id": role_id}
        )
        await self.user_repo.db.commit()
        return result.rowcount > 0
    
    async def remove_role(self, user_id: int, role_id: int) -> bool:
        """Удаление роли у пользователя"""
        from sqlalchemy import text
        result = await self.user_repo.db.execute(
            text("DELETE FROM users_roles WHERE user_id = :user_id AND role_id = :role_id"),
            {"user_id": user_id, "role_id": role_id}
        )
        await self.user_repo.db.commit()
        return result.rowcount > 0
    
    async def assign_project(self, user_id: int, project_id: int) -> bool:
        """Назначение проекта пользователю"""
        from sqlalchemy import text
        result = await self.user_repo.db.execute(
            text("INSERT INTO user_projects (user_id, project_id) VALUES (:user_id, :project_id)"),
            {"user_id": user_id, "project_id": project_id}
        )
        await self.user_repo.db.commit()
        return result.rowcount > 0
    
    async def remove_project(self, user_id: int, project_id: int) -> bool:
        """Удаление проекта у пользователя"""
        from sqlalchemy import text
        result = await self.user_repo.db.execute(
            text("DELETE FROM user_projects WHERE user_id = :user_id AND project_id = :project_id"),
            {"user_id": user_id, "project_id": project_id}
        )
        await self.user_repo.db.commit()
        return result.rowcount > 0
