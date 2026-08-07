# app/services/user_service.py (ОБНОВЛЁННАЯ ВЕРСИЯ)
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.schemas.user import UserResponse, UserCreate, UserUpdate, user_to_response, get_user_status_from_model
from app.schemas.admin import UserAdminResponse, user_to_admin_response
from app.models.user import User


class UserService:
    def __init__(self, user_repo: UserRepository, role_repo: RoleRepository):
        self.user_repo = user_repo
        self.role_repo = role_repo
    
    # ========== Базовые CRUD операции ==========
    
    async def get_user_by_id(self, user_id: int, include_deleted: bool = False) -> Optional[UserResponse]:
        """Получить пользователя по ID"""
        user = await self.user_repo.get_by_id(user_id, include_deleted=include_deleted)
        if not user:
            return None
        
        # Загружаем роли и проекты
        roles = await user.awaitable_attrs.roles
        projects = await user.awaitable_attrs.projects
        
        role_titles = [r.role_title for r in roles] if roles else []
        project_titles = [p.project_title for p in projects] if projects else []
        
        return user_to_response(user, role_titles, project_titles)
    
    async def get_user_by_email(self, email: str, include_deleted: bool = False) -> Optional[User]:
        """Получить пользователя по email (возвращает модель)"""
        return await self.user_repo.get_by_email(email, include_deleted=include_deleted)
    
    async def get_user_by_username(self, username: str, include_deleted: bool = False) -> Optional[User]:
        """Получить пользователя по имени пользователя"""
        return await self.user_repo.get_by_username(username, include_deleted=include_deleted)
    
    async def get_all_users(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        include_deleted: bool = False,
        only_active: bool = True
    ) -> List[UserResponse]:
        """Получить список всех пользователей"""
        users = await self.user_repo.get_all(skip, limit, include_deleted, only_active)
        result = []
        
        for user in users:
            roles = await user.awaitable_attrs.roles
            projects = await user.awaitable_attrs.projects
            role_titles = [r.role_title for r in roles] if roles else []
            project_titles = [p.project_title for p in projects] if projects else []
            result.append(user_to_response(user, role_titles, project_titles))
        
        return result
    
    # ========== Создание пользователя ==========
    
    async def create_user(self, user_data: UserCreate, password_hash: str) -> UserResponse:
        """Создать нового пользователя"""
        # Проверка на существование
        existing_email = await self.user_repo.get_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        existing_username = await self.user_repo.get_by_username(user_data.user_name)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username already exists"
            )
        
        # Создаём пользователя (status больше нет)
        user = await self.user_repo.create(
            email=user_data.email,
            username=user_data.user_name,
            hashed_password=password_hash,
            gender=user_data.gender,
            birth_date=user_data.birth_date,
            dept_code=user_data.dept_code,
            phone_work=user_data.phone_work,
            phone_mobile=user_data.phone_mobile
        )
        
        # Загружаем роли и проекты (пустые для нового пользователя)
        roles = await user.awaitable_attrs.roles
        projects = await user.awaitable_attrs.projects
        role_titles = [r.role_title for r in roles] if roles else []
        project_titles = [p.project_title for p in projects] if projects else []
        
        return user_to_response(user, role_titles, project_titles)
    
    # ========== Обновление пользователя ==========
    
    async def update_user(self, user_id: int, update_data: Dict[str, Any]) -> Optional[UserResponse]:
        """Обновить данные пользователя"""
        # Запрещаем обновление敏感 полей
        forbidden = ['user_id', 'password_hash', 'created_at', 'deleted_at', 'blocked_at']
        filtered_data = {k: v for k, v in update_data.items() if k not in forbidden}
        
        user = await self.user_repo.update(user_id, filtered_data)
        if not user:
            return None
        
        roles = await user.awaitable_attrs.roles
        projects = await user.awaitable_attrs.projects
        role_titles = [r.role_title for r in roles] if roles else []
        project_titles = [p.project_title for p in projects] if projects else []
        
        return user_to_response(user, role_titles, project_titles)
    
    # ========== Удаление и восстановление ==========
    
    async def delete_user(self, user_id: int, soft: bool = True) -> bool:
        """
        Удалить пользователя
        soft: True - мягкое удаление, False - физическое
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
        
        return await self.user_repo.delete(user_id, soft=soft)
    
    async def restore_user(self, user_id: int) -> Optional[UserResponse]:
        """Восстановить мягко удалённого пользователя"""
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user or user.deleted_at is None:
            return None
        
        restored = await self.user_repo.restore(user_id)
        if not restored:
            return None
        
        roles = await user.awaitable_attrs.roles
        projects = await user.awaitable_attrs.projects
        role_titles = [r.role_title for r in roles] if roles else []
        project_titles = [p.project_title for p in projects] if projects else []
        
        return user_to_response(user, role_titles, project_titles)
    
    # ========== Блокировка и разблокировка ==========
    
    async def block_user(
        self, 
        user_id: int, 
        reason: str, 
        blocked_by: int,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Заблокировать пользователя"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
        
        return await self.user_repo.block_user(user_id, reason, blocked_by, expires_at)
    
    async def unblock_user(self, user_id: int) -> bool:
        """Разблокировать пользователя"""
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            return False
        
        return await self.user_repo.unblock_user(user_id)
    
    async def is_user_blocked(self, user_id: int) -> bool:
        """Проверить, заблокирован ли пользователь"""
        return await self.user_repo.is_user_blocked(user_id)
    
    # ========== Управление ролями ==========
    
    async def assign_role(self, user_id: int, role_id: int) -> bool:
        """Назначить роль пользователю"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
        
        return await self.role_repo.assign_role_to_user(user_id, role_id)
    
    async def assign_role_by_code(self, user_id: int, role_code: str) -> bool:
        """Назначить роль пользователю по коду"""
        role = await self.role_repo.get_by_code(role_code)
        if not role:
            return False
        
        return await self.assign_role(user_id, role.role_id)
    
    async def remove_role(self, user_id: int, role_id: int) -> bool:
        """Удалить роль у пользователя"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
        
        return await self.role_repo.remove_role_from_user(user_id, role_id)
    
    async def get_user_roles(self, user_id: int) -> List[str]:
        """Получить список ролей пользователя"""
        return await self.user_repo.get_user_roles(user_id)
    
    async def get_user_role_objects(self, user_id: int) -> List:
        """Получить объекты ролей пользователя"""
        return await self.role_repo.get_user_roles(user_id)
    
    # ========== Дополнительные методы ==========
    
    async def get_users_by_dept(self, dept_code: str) -> List[UserResponse]:
        """Получить пользователей по отделу"""
        # TODO: реализовать в репозитории
        users = await self.user_repo.get_by_dept(dept_code) if hasattr(self.user_repo, 'get_by_dept') else []
        result = []
        for user in users:
            roles = await user.awaitable_attrs.roles
            projects = await user.awaitable_attrs.projects
            role_titles = [r.role_title for r in roles] if roles else []
            project_titles = [p.project_title for p in projects] if projects else []
            result.append(user_to_response(user, role_titles, project_titles))
        return result
    
    async def get_blocked_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """Получить список заблокированных пользователей"""
        users = await self.user_repo.get_blocked_users(skip, limit)
        result = []
        for user in users:
            roles = await user.awaitable_attrs.roles
            projects = await user.awaitable_attrs.projects
            role_titles = [r.role_title for r in roles] if roles else []
            project_titles = [p.project_title for p in projects] if projects else []
            result.append(user_to_response(user, role_titles, project_titles))
        return result
    
    async def get_deleted_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """Получить список удалённых пользователей"""
        users = await self.user_repo.get_deleted_users(skip, limit)
        result = []
        for user in users:
            roles = await user.awaitable_attrs.roles
            projects = await user.awaitable_attrs.projects
            role_titles = [r.role_title for r in roles] if roles else []
            project_titles = [p.project_title for p in projects] if projects else []
            result.append(user_to_response(user, role_titles, project_titles))
        return result
