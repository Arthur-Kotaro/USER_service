# app/services/admin_service.py (ОБНОВЛЁННАЯ ВЕРСИЯ)
from typing import Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, or_, select
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.role import Role
from app.models.project import Project
from app.models.login_history import LoginHistory
from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.login_history_repo import LoginHistoryRepository
from app.utils.hasher import hash_password
from app.schemas.admin import (
    UserAdminUpdate, UserAdminResponse, AdminStatsResponse, 
    user_to_admin_response, BlockUserRequest, UnblockUserRequest
)
from app.schemas.user import get_user_status_from_model


class AdminService:
    def __init__(
        self, 
        user_repo: UserRepository,
        role_repo: RoleRepository,
        login_history_repo: LoginHistoryRepository
    ):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.login_history_repo = login_history_repo
    
    # ========== Получение пользователей ==========
    
    async def get_user_by_username(self, username: str, include_deleted: bool = False) -> Optional[User]:
        """Получить пользователя по имени"""
        return await self.user_repo.get_by_username(username, include_deleted=include_deleted)
    
    async def get_user_by_email(self, email: str, include_deleted: bool = False) -> Optional[User]:
        """Получить пользователя по email"""
        return await self.user_repo.get_by_email(email, include_deleted=include_deleted)
    
    async def get_user_by_id(self, user_id: int, include_deleted: bool = False) -> Optional[User]:
        """Получить пользователя по ID"""
        return await self.user_repo.get_by_id(user_id, include_deleted=include_deleted)
    
    async def get_all_users(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        include_deleted: bool = False
    ) -> Tuple[List[UserAdminResponse], int]:
        """Получить всех пользователей с фильтрацией"""
        # Строим фильтр
        filter_expr = []
        
        if status_filter:
            if status_filter == "active":
                filter_expr.append(User.blocked_at.is_(None))
                filter_expr.append(User.deleted_at.is_(None))
            elif status_filter == "blocked":
                filter_expr.append(User.blocked_at.is_not(None))
                filter_expr.append(User.deleted_at.is_(None))
            elif status_filter == "deleted":
                filter_expr.append(User.deleted_at.is_not(None))
                include_deleted = True
        
        if search:
            filter_expr.append(
                or_(
                    User.user_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")
                )
            )
        
        # Получаем пользователей
        query = select(User).options(
            selectinload(User.roles), 
            selectinload(User.projects)
        )
        
        if filter_expr:
            query = query.where(and_(*filter_expr))
        
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        
        query = query.offset(skip).limit(limit)
        
        # Выполняем запрос
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            result = await db.execute(query)
            users = result.unique().scalars().all()
            
            # Подсчёт общего количества
            count_query = select(func.count()).select_from(User)
            if filter_expr:
                count_query = count_query.where(and_(*filter_expr))
            if not include_deleted:
                count_query = count_query.where(User.deleted_at.is_(None))
            count_result = await db.execute(count_query)
            total = count_result.scalar()
        
        # Преобразуем в ответ
        admin_responses = []
        for user in users:
            roles = await user.awaitable_attrs.roles
            projects = await user.awaitable_attrs.projects
            role_titles = [r.role_title for r in roles] if roles else []
            project_titles = [p.project_title for p in projects] if projects else []
            admin_responses.append(user_to_admin_response(user, role_titles, project_titles))
        
        return admin_responses, total
    
    # ========== Создание и обновление пользователей ==========
    
    async def create_user(self, user_data: UserAdminUpdate, password_hash: str) -> User:
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
        
        # Создаём пользователя (status удалён)
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
        
        return user
    
    async def update_user(self, user_id: int, user_data: UserAdminUpdate) -> Optional[User]:
        """Обновить пользователя"""
        user = await self.get_user_by_id(user_id, include_deleted=True)
        if not user:
            return None
        
        update_dict = {}
        
        if user_data.user_name is not None:
            update_dict['user_name'] = user_data.user_name
        if user_data.email is not None:
            update_dict['email'] = user_data.email
        if user_data.gender is not None:
            update_dict['gender'] = user_data.gender
        if user_data.birth_date is not None:
            update_dict['birth_date'] = user_data.birth_date
        if user_data.dept_code is not None:
            update_dict['dept_code'] = user_data.dept_code
        if user_data.phone_work is not None:
            update_dict['phone_work'] = user_data.phone_work
        if user_data.phone_mobile is not None:
            update_dict['phone_mobile'] = user_data.phone_mobile
        
        # Управление блокировкой через отдельные методы
        if user_data.block_reason is not None:
            update_dict['blocked_reason'] = user_data.block_reason
        if user_data.block_expires_at is not None:
            update_dict['block_expires_at'] = user_data.block_expires_at
        
        if update_dict:
            user = await self.user_repo.update(user_id, update_dict)
        
        return user
    
    # ========== Удаление и восстановление ==========
    
    async def delete_user(self, user_id: int, soft: bool = True) -> bool:
        """Удаление пользователя (soft delete по умолчанию)"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        return await self.user_repo.delete(user_id, soft=soft)
    
    async def restore_user(self, user_id: int) -> Optional[User]:
        """Восстановление мягко удалённого пользователя"""
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user or user.deleted_at is None:
            return None
        
        restored = await self.user_repo.restore(user_id)
        return user if restored else None
    
    # ========== Блокировка и разблокировка ==========
    
    async def block_user(
        self, 
        user_id: int, 
        admin_id: int, 
        reason: str, 
        expires_at: Optional[datetime] = None
    ) -> Optional[User]:
        """Заблокировать пользователя"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Нельзя заблокировать уже удалённого
        if user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot block a deleted user"
            )
        
        success = await self.user_repo.block_user(user_id, reason, admin_id, expires_at)
        if success:
            return await self.get_user_by_id(user_id)
        return None
    
    async def unblock_user(self, user_id: int, admin_id: int, reason: Optional[str] = None) -> Optional[User]:
        """Разблокировать пользователя"""
        user = await self.get_user_by_id(user_id, include_deleted=True)
        if not user:
            return None
        
        success = await self.user_repo.unblock_user(user_id)
        if success:
            # TODO: записать в историю разблокировки
            return await self.get_user_by_id(user_id)
        return None
    
    # ========== Управление ролями ==========
    
    async def assign_role(self, user_id: int, role_id: int) -> bool:
        """Назначить роль пользователю"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        return await self.role_repo.assign_role_to_user(user_id, role_id)
    
    async def assign_role_by_code(self, user_id: int, role_code: str) -> bool:
        """Назначить роль по коду"""
        role = await self.role_repo.get_by_code(role_code)
        if not role:
            return False
        
        return await self.assign_role(user_id, role.role_id)
    
    async def remove_role(self, user_id: int, role_id: int) -> bool:
        """Удалить роль у пользователя"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        return await self.role_repo.remove_role_from_user(user_id, role_id)
    
    # ========== Управление проектами ==========
    
    async def assign_project(self, user_id: int, project_id: int) -> bool:
        """Назначить проект пользователю"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # TODO: добавить метод в репозиторий
        # return await self.user_repo.assign_project(user_id, project_id)
        return True
    
    async def remove_project(self, user_id: int, project_id: int) -> bool:
        """Удалить проект у пользователя"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # TODO: добавить метод в репозиторий
        return True
    
    # ========== Статистика ==========
    
    async def get_stats(self) -> AdminStatsResponse:
        """Получить статистику"""
        from app.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            # Общее количество
            total_result = await db.execute(select(func.count()).select_from(User))
            total_users = total_result.scalar()
            
            # Активные (не заблокированы, не удалены)
            active_result = await db.execute(
                select(func.count()).select_from(User)
                .where(User.blocked_at.is_(None))
                .where(User.deleted_at.is_(None))
            )
            active_users = active_result.scalar()
            
            # Заблокированные
            blocked_result = await db.execute(
                select(func.count()).select_from(User)
                .where(User.blocked_at.is_not(None))
                .where(User.deleted_at.is_(None))
            )
            blocked_users = blocked_result.scalar()
            
            # Удалённые
            deleted_result = await db.execute(
                select(func.count()).select_from(User)
                .where(User.deleted_at.is_not(None))
            )
            deleted_users = deleted_result.scalar()
            
            # Администраторы (роль admin)
            admin_role = await db.execute(
                select(Role).where(Role.role_title == "admin")
            )
            admin_role_obj = admin_role.scalar_one_or_none()
            
            if admin_role_obj:
                admin_users = len(admin_role_obj.users)
            else:
                admin_users = 0
            
            regular_users = total_users - admin_users
            
            # Пользователи с временным паролем
            temp_password_result = await db.execute(
                select(func.count()).select_from(User)
                .where(User.temp_password.is_not(None))
                .where(User.temp_password_expires_at > datetime.now(timezone.utc))
                .where(User.deleted_at.is_(None))
            )
            users_with_temp_password = temp_password_result.scalar()
            
            # Пароль истекает скоро (< 7 дней)
            expiring_soon = datetime.now(timezone.utc) + timedelta(days=7)
            expiring_result = await db.execute(
                select(func.count()).select_from(User)
                .where(User.password_updated_at <= expiring_soon)
                .where(User.deleted_at.is_(None))
            )
            users_password_expiring_soon = expiring_result.scalar()
        
        return AdminStatsResponse(
            total_users=total_users,
            active_users=active_users,
            blocked_users=blocked_users,
            deleted_users=deleted_users,
            admin_users=admin_users,
            regular_users=regular_users,
            users_with_temp_password=users_with_temp_password,
            users_password_expiring_soon=users_password_expiring_soon
        )
    
    # ========== История входов ==========
    
    async def get_user_login_history(self, user_id: int, limit: int = 50) -> List[dict]:
        """Получить историю входов пользователя"""
        history = await self.login_history_repo.get_by_user(user_id, limit=limit)
        return [
            {
                "login_at": h.login_at,
                "ip_address": str(h.ip_address) if h.ip_address else None,
                "user_agent": h.user_agent,
                "login_status": h.login_status,
                "failure_reason": h.failure_reason
            }
            for h in history
        ]
