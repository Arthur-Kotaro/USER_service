# app/services/admin_service.py (ОБНОВЛЕННАЯ ВЕРСИЯ - БЕЗ ПРОЕКТОВ)
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException, status

from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.login_history_repo import LoginHistoryRepository
from app.schemas.admin import (
    UserAdminUpdate, UserAdminResponse, UserListResponse,
    BlockUserRequest, BlockUserResponse, DeletedUserResponse,
    AdminStatsResponse, user_to_admin_response
)
from app.schemas.user import UserStatus
from app.models.user import User
from app.utils.hasher import hash_password


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

    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        only_active: bool = True
    ) -> UserListResponse:
        """Получить список пользователей с пагинацией"""
        users = await self.user_repo.get_all(skip, limit, include_deleted, only_active)
        total = len(users)  # В реальности лучше сделать отдельный запрос для подсчета
        
        user_responses = []
        for user in users:
            roles = [r.role_title for r in user.roles] if user.roles else []
            user_responses.append(user_to_admin_response(user, roles))
        
        return UserListResponse(total=total, users=user_responses)

    async def get_user_by_id(self, user_id: int) -> Optional[UserAdminResponse]:
        """Получить пользователя по ID"""
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            return None
        roles = [r.role_title for r in user.roles] if user.roles else []
        return user_to_admin_response(user, roles)

    async def update_user_by_admin(
        self,
        user_id: int,
        update_data: UserAdminUpdate,
        admin_id: int
    ) -> Optional[UserAdminResponse]:
        """Обновление пользователя администратором"""
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            return None
        
        # Нельзя редактировать супер-админа обычному админу
        if user.is_super_admin:
            current_admin = await self.user_repo.get_by_id(admin_id)
            if current_admin and not current_admin.is_super_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot modify super admin"
                )
        
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_user = await self.user_repo.update(user_id, update_dict)
        if not updated_user:
            return None
        
        roles = [r.role_title for r in updated_user.roles] if updated_user.roles else []
        return user_to_admin_response(updated_user, roles)

    async def block_user(
        self,
        user_id: int,
        block_data: BlockUserRequest,
        admin_id: int
    ) -> BlockUserResponse:
        """Блокировка пользователя"""
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.deleted_at is not None:
            raise HTTPException(status_code=400, detail="User is already deleted")
        
        if user.is_super_admin:
            current_admin = await self.user_repo.get_by_id(admin_id)
            if current_admin and not current_admin.is_super_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot block super admin"
                )
        
        blocked = await self.user_repo.block_user(
            user_id=user_id,
            reason=block_data.reason,
            blocked_by=admin_id,
            expires_at=block_data.expires_at
        )
        
        if not blocked:
            raise HTTPException(status_code=400, detail="Failed to block user")
        
        # Обновляем пользователя для получения данных
        user = await self.user_repo.get_by_id(user_id)
        
        return BlockUserResponse(
            user_id=user.user_id,
            user_name=user.user_name,
            blocked_at=user.blocked_at,
            blocked_reason=user.blocked_reason,
            block_expires_at=user.block_expires_at,
            blocked_by=admin_id,
            blocked_by_name="Admin"  # Можно подставить имя админа
        )

    async def unblock_user(self, user_id: int) -> bool:
        """Разблокировка пользователя"""
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            return False
        
        return await self.user_repo.unblock_user(user_id)

    async def soft_delete_user(
        self,
        user_id: int,
        admin_id: int,
        reason: Optional[str] = None
    ) -> bool:
        """Мягкое удаление пользователя"""
        user = await self.user_repo.get_by_id(user_id, include_deleted=True)
        if not user:
            return False
        
        if user.is_super_admin:
            current_admin = await self.user_repo.get_by_id(admin_id)
            if current_admin and not current_admin.is_super_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot delete super admin"
                )
        
        return await self.user_repo.delete(user_id, soft=True)

    async def restore_user(self, user_id: int) -> bool:
        """Восстановление пользователя"""
        return await self.user_repo.restore(user_id)

    async def get_deleted_users(self, skip: int = 0, limit: int = 100) -> List[DeletedUserResponse]:
        """Получить список удаленных пользователей"""
        users = await self.user_repo.get_deleted_users(skip, limit)
        result = []
        for user in users:
            result.append(DeletedUserResponse(
                user_id=user.user_id,
                user_name=user.user_name,
                email=user.email,
                deleted_at=user.deleted_at,
                deleted_reason=None,  # Можно добавить поле в модель
                deleted_by=None,
                deleted_by_name=None
            ))
        return result

    async def get_stats(self) -> AdminStatsResponse:
        """Получить статистику"""
        # Это упрощенная версия — в реальности нужно делать отдельные запросы
        all_users = await self.user_repo.get_all(0, 10000, include_deleted=True)
        
        total = len(all_users)
        active = sum(1 for u in all_users if u.deleted_at is None and u.blocked_at is None)
        blocked = sum(1 for u in all_users if u.blocked_at is not None)
        deleted = sum(1 for u in all_users if u.deleted_at is not None)
        
        # Подсчет ролей
        admin_count = 0
        super_admin_count = 0
        regular_count = 0
        
        for user in all_users:
            if user.deleted_at is None:
                if user.is_super_admin:
                    super_admin_count += 1
                elif user.has_role("admin"):
                    admin_count += 1
                else:
                    regular_count += 1
        
        return AdminStatsResponse(
            total_users=total,
            active_users=active,
            blocked_users=blocked,
            locked_users=0,
            deleted_users=deleted,
            admin_users=admin_count,
            super_admin_users=super_admin_count,
            regular_users=regular_count,
            users_with_temp_password=0,
            users_password_expiring_soon=0
        )

    async def assign_role(self, user_id: int, role_id: int) -> bool:
        """Назначить роль пользователю"""
        return await self.user_repo.assign_role(user_id, role_id)

    async def remove_role(self, user_id: int, role_id: int) -> bool:
        """Удалить роль у пользователя"""
        return await self.user_repo.remove_role(user_id, role_id)

    async def reset_user_password(self, user_id: int, new_password: str) -> bool:
        """Сброс пароля пользователя администратором"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False
        
        if user.deleted_at is not None:
            return False
        
        hashed = hash_password(new_password)
        return await self.user_repo.update_password(user_id, hashed)
