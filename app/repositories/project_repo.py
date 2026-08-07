# app/repositories/project_repo.py (НОВЫЙ ФАЙЛ)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from app.models.project import Project, ProjectStatus, user_projects
from app.models.user import User


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ========== Базовые CRUD операции ==========
    
    async def get_by_id(self, project_id: int) -> Optional[Project]:
        """Получение проекта по ID"""
        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.users))
            .where(Project.project_id == project_id)
        )
        return result.unique().scalar_one_or_none()
    
    async def get_by_title(self, title: str) -> Optional[Project]:
        """Получение проекта по названию"""
        result = await self.db.execute(
            select(Project).where(Project.project_title == title)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        include_cancelled: bool = False
    ) -> List[Project]:
        """Получение списка проектов с фильтрацией"""
        query = select(Project)
        
        if status:
            query = query.where(Project.status == status)
        
        if not include_cancelled:
            query = query.where(Project.status != ProjectStatus.CANCELLED)
        
        query = query.offset(skip).limit(limit).order_by(Project.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create(
        self, 
        title: str, 
        description: Optional[str] = None,
        status: ProjectStatus = ProjectStatus.DRAFT
    ) -> Project:
        """Создание нового проекта"""
        project = Project(
            project_title=title,
            project_description=description,
            status=status
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project
    
    async def update(self, project_id: int, update_data: Dict[str, Any]) -> Optional[Project]:
        """Обновление проекта"""
        project = await self.get_by_id(project_id)
        if not project:
            return None
        
        for key, value in update_data.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)
        
        await self.db.commit()
        await self.db.refresh(project)
        return project
    
    async def delete(self, project_id: int) -> bool:
        """Удаление проекта (физическое)"""
        project = await self.get_by_id(project_id)
        if not project:
            return False
        
        await self.db.delete(project)
        await self.db.commit()
        return True
    
    # ========== Управление статусом ==========
    
    async def update_status(self, project_id: int, new_status: ProjectStatus) -> Optional[Project]:
        """Обновление статуса проекта"""
        project = await self.get_by_id(project_id)
        if not project:
            return None
        
        project.status = new_status
        await self.db.commit()
        await self.db.refresh(project)
        return project
    
    async def get_by_status(self, status: ProjectStatus, skip: int = 0, limit: int = 100) -> List[Project]:
        """Получение проектов по статусу"""
        result = await self.db.execute(
            select(Project)
            .where(Project.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(Project.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_active_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """Получение активных проектов"""
        return await self.get_by_status(ProjectStatus.ACTIVE, skip, limit)
    
    async def get_completed_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """Получение завершённых проектов"""
        return await self.get_by_status(ProjectStatus.COMPLETED, skip, limit)
    
    # ========== Управление участниками ==========
    
    async def add_user(self, project_id: int, user_id: int, role: str = "member") -> bool:
        """Добавление пользователя в проект"""
        # Проверяем, не состоит ли уже пользователь в проекте
        result = await self.db.execute(
            select(user_projects).where(
                and_(
                    user_projects.c.project_id == project_id,
                    user_projects.c.user_id == user_id
                )
            )
        )
        if result.first():
            return False
        
        # Добавляем пользователя
        await self.db.execute(
            user_projects.insert().values(
                project_id=project_id,
                user_id=user_id,
                project_role=role,
                joined_at=datetime.now(timezone.utc)
            )
        )
        await self.db.commit()
        return True
    
    async def remove_user(self, project_id: int, user_id: int) -> bool:
        """Удаление пользователя из проекта"""
        result = await self.db.execute(
            select(user_projects).where(
                and_(
                    user_projects.c.project_id == project_id,
                    user_projects.c.user_id == user_id
                )
            )
        )
        if not result.first():
            return False
        
        # Удаляем пользователя (или устанавливаем left_at)
        await self.db.execute(
            user_projects.delete().where(
                and_(
                    user_projects.c.project_id == project_id,
                    user_projects.c.user_id == user_id
                )
            )
        )
        await self.db.commit()
        return True
    
    async def update_user_role(self, project_id: int, user_id: int, new_role: str) -> bool:
        """Обновление роли пользователя в проекте"""
        result = await self.db.execute(
            update(user_projects)
            .where(
                and_(
                    user_projects.c.project_id == project_id,
                    user_projects.c.user_id == user_id
                )
            )
            .values(project_role=new_role)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def get_users(self, project_id: int) -> List[User]:
        """Получение всех участников проекта"""
        result = await self.db.execute(
            select(User)
            .join(user_projects)
            .where(user_projects.c.project_id == project_id)
        )
        return result.scalars().all()
    
    async def get_user_roles_in_project(self, project_id: int, user_id: int) -> Optional[str]:
        """Получение роли пользователя в проекте"""
        result = await self.db.execute(
            select(user_projects.c.project_role)
            .where(
                and_(
                    user_projects.c.project_id == project_id,
                    user_projects.c.user_id == user_id
                )
            )
        )
        row = result.first()
        return row[0] if row else None
    
    async def is_user_in_project(self, project_id: int, user_id: int) -> bool:
        """Проверка, является ли пользователь участником проекта"""
        result = await self.db.execute(
            select(user_projects).where(
                and_(
                    user_projects.c.project_id == project_id,
                    user_projects.c.user_id == user_id
                )
            )
        )
        return result.first() is not None
    
    # ========== Проекты пользователя ==========
    
    async def get_user_projects(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Project]:
        """Получение всех проектов пользователя"""
        result = await self.db.execute(
            select(Project)
            .join(user_projects)
            .where(user_projects.c.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_user_projects_by_status(self, user_id: int, status: ProjectStatus) -> List[Project]:
        """Получение проектов пользователя по статусу"""
        result = await self.db.execute(
            select(Project)
            .join(user_projects)
            .where(
                and_(
                    user_projects.c.user_id == user_id,
                    Project.status == status
                )
            )
        )
        return result.scalars().all()
    
    # ========== Поиск проектов ==========
    
    async def search_projects(self, query: str, skip: int = 0, limit: int = 100) -> List[Project]:
        """Поиск проектов по названию или описанию"""
        result = await self.db.execute(
            select(Project)
            .where(
                or_(
                    Project.project_title.ilike(f"%{query}%"),
                    Project.project_description.ilike(f"%{query}%")
                )
            )
            .where(Project.status != ProjectStatus.CANCELLED)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    # ========== Статистика ==========
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики по проектам"""
        result = await self.db.execute(
            select(
                Project.status,
                func.count(Project.project_id)
            )
            .group_by(Project.status)
        )
        
        stats = {
            "total": 0,
            "draft": 0,
            "active": 0,
            "suspended": 0,
            "completed": 0,
            "cancelled": 0
        }
        
        for status, count in result.all():
            status_value = status.value if hasattr(status, 'value') else status
            stats[status_value] = count
            stats["total"] += count
        
        return stats
