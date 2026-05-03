# app/services/admin_service.py
from typing import Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.user import User
from app.models.role import Role
from app.models.project import Project
from app.repositories.user_repo import UserRepository
from app.utils.hasher import hash_password
from app.schemas.admin import UserAdminUpdate, UserAdminResponse, AdminStatsResponse

class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Получить пользователя по имени"""
        return await self.user_repo.get_by_username(username)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        return await self.user_repo.get_by_email(email)
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        return await self.user_repo.get_by_id(user_id)
    
    async def create_user(self, user_data: UserAdminUpdate) -> User:
        """Создать нового пользователя"""
        hashed_password = hash_password("temp123")  # Временный пароль, нужно будет сменить
        
        user = User(
            user_name=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            status="active",
            password_updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def get_all_users(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        status_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """Получить всех пользователей с фильтрацией"""
        query = self.db.query(User)
        
        if status_filter:
            query = query.filter(User.status == status_filter)
        
        if search:
            query = query.filter(
                or_(
                    User.user_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")
                )
            )
        
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        
        return users, total
    
    async def update_user(self, user_id: int, user_data: UserAdminUpdate) -> Optional[User]:
        """Обновить пользователя"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        if user_data.username is not None:
            user.user_name = user_data.username
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.is_active is not None:
            user.status = "active" if user_data.is_active else "archived"
        if user_data.is_admin is not None:
            # Здесь нужно управление ролями
            pass
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def delete_user(self, user_id: int) -> bool:
        """Мягкое удаление пользователя (архивация)"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.status = "archived"
        self.db.commit()
        return True
    
    async def block_user(
        self, 
        user_id: int, 
        admin_id: int, 
        reason: Optional[str] = None, 
        expires_at: Optional[datetime] = None
    ) -> Optional[User]:
        """Заблокировать пользователя"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.status = "blocked"
        user.blocked_at = datetime.now(timezone.utc)
        user.blocked_reason = reason
        user.blocked_by = admin_id
        user.block_expires_at = expires_at
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def unblock_user(self, user_id: int) -> Optional[User]:
        """Разблокировать пользователя"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.status = "active"
        user.blocked_at = None
        user.blocked_reason = None
        user.blocked_by = None
        user.block_expires_at = None
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def assign_role(self, user_id: int, role_id: int) -> bool:
        """Назначить роль пользователю"""
        user = await self.get_user_by_id(user_id)
        role = self.db.query(Role).filter(Role.role_id == role_id).first()
        
        if not user or not role:
            return False
        
        if role not in user.roles:
            user.roles.append(role)
            self.db.commit()
        
        return True
    
    async def remove_role(self, user_id: int, role_id: int) -> bool:
        """Удалить роль у пользователя"""
        user = await self.get_user_by_id(user_id)
        role = self.db.query(Role).filter(Role.role_id == role_id).first()
        
        if not user or not role:
            return False
        
        if role in user.roles:
            user.roles.remove(role)
            self.db.commit()
        
        return True
    
    async def assign_project(self, user_id: int, project_id: int) -> bool:
        """Назначить проект пользователю"""
        user = await self.get_user_by_id(user_id)
        project = self.db.query(Project).filter(Project.project_id == project_id).first()
        
        if not user or not project:
            return False
        
        if project not in user.projects:
            user.projects.append(project)
            self.db.commit()
        
        return True
    
    async def remove_project(self, user_id: int, project_id: int) -> bool:
        """Удалить проект у пользователя"""
        user = await self.get_user_by_id(user_id)
        project = self.db.query(Project).filter(Project.project_id == project_id).first()
        
        if not user or not project:
            return False
        
        if project in user.projects:
            user.projects.remove(project)
            self.db.commit()
        
        return True
    
    async def get_stats(self) -> AdminStatsResponse:
        """Получить статистику"""
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.status == "active").count()
        inactive_users = self.db.query(User).filter(User.status == "archived").count()
        
        admin_role = self.db.query(Role).filter(Role.role_title == "admin").first()
        if admin_role:
            admin_users = len(admin_role.users)
        else:
            admin_users = 0
        
        regular_users = total_users - admin_users
        
        return AdminStatsResponse(
            total_users=total_users,
            active_users=active_users,
            inactive_users=inactive_users,
            admin_users=admin_users,
            regular_users=regular_users
        )
    
    async def get_daily_registrations(self, days: int) -> List[dict]:
        """Получить статистику регистраций по дням"""
        from datetime import timedelta
        
        result = []
        for i in range(days):
            date = datetime.now(timezone.utc).date() - timedelta(days=i)
            count = self.db.query(User).filter(
                func.date(User.created_at) == date
            ).count()
            result.append({"date": date.isoformat(), "count": count})
        
        return result
