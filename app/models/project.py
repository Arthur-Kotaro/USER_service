# app/models/project.py (ОБНОВЛЁННАЯ ВЕРСИЯ)
from sqlalchemy import Column, Integer, BigInteger, String, Text, Table, ForeignKey, Enum, Index, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

# Ассоциативная таблица для связи many-to-many между User и Project
user_projects = Table(
    "user_projects",
    Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("project_id", Integer, ForeignKey("projects.project_id", ondelete="CASCADE"), primary_key=True),
)


class ProjectStatus(str, enum.Enum):
    """Статусы проекта"""
    DRAFT = "draft"          # создан (черновик)
    ACTIVE = "active"        # активен
    SUSPENDED = "suspended"  # приостановлен
    COMPLETED = "completed"  # завершён
    CANCELLED = "cancelled"  # отменён


class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(Integer, primary_key=True, autoincrement=True)
    project_title = Column(String(100), nullable=False, unique=True)
    project_description = Column(Text, nullable=True)
    
    # НОВОЕ ПОЛЕ: статус проекта
    status = Column(
        Enum(ProjectStatus, name="project_status_type", create_type=True),
        nullable=False,
        default=ProjectStatus.DRAFT
    )
    
    # Аудит
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Связи
    users = relationship("User", secondary=user_projects, back_populates="projects")
    
    # Индексы
    __table_args__ = (
        Index("idx_projects_status", "status"),
        Index("idx_projects_status_active", "status", postgresql_where=(status == ProjectStatus.ACTIVE)),
        Index("idx_projects_created_at", "created_at"),
        Index("idx_projects_updated_at", "updated_at"),
    )
    
    # ========== Свойства ==========
    
    @property
    def is_active(self) -> bool:
        """Проект активен"""
        return self.status == ProjectStatus.ACTIVE
    
    @property
    def is_draft(self) -> bool:
        """Проект в черновике"""
        return self.status == ProjectStatus.DRAFT
    
    @property
    def is_suspended(self) -> bool:
        """Проект приостановлен"""
        return self.status == ProjectStatus.SUSPENDED
    
    @property
    def is_completed(self) -> bool:
        """Проект завершён"""
        return self.status == ProjectStatus.COMPLETED
    
    @property
    def is_cancelled(self) -> bool:
        """Проект отменён"""
        return self.status == ProjectStatus.CANCELLED
    
    @property
    def can_be_edited(self) -> bool:
        """Можно ли редактировать проект"""
        return self.status in [ProjectStatus.DRAFT, ProjectStatus.ACTIVE]
    
    @property
    def is_visible(self) -> bool:
        """Видим ли проект для пользователей (не отменён и не завершён)"""
        return self.status not in [ProjectStatus.CANCELLED, ProjectStatus.COMPLETED]
    
    # ========== Методы ==========
    
    def activate(self) -> None:
        """Активировать проект"""
        if self.status == ProjectStatus.DRAFT:
            self.status = ProjectStatus.ACTIVE
        else:
            raise ValueError(f"Cannot activate project with status '{self.status.value}'")
    
    def suspend(self) -> None:
        """Приостановить проект"""
        if self.status == ProjectStatus.ACTIVE:
            self.status = ProjectStatus.SUSPENDED
        else:
            raise ValueError(f"Cannot suspend project with status '{self.status.value}'")
    
    def resume(self) -> None:
        """Возобновить проект (из приостановленного в активный)"""
        if self.status == ProjectStatus.SUSPENDED:
            self.status = ProjectStatus.ACTIVE
        else:
            raise ValueError(f"Cannot resume project with status '{self.status.value}'")
    
    def complete(self) -> None:
        """Завершить проект"""
        if self.status in [ProjectStatus.ACTIVE, ProjectStatus.SUSPENDED]:
            self.status = ProjectStatus.COMPLETED
        else:
            raise ValueError(f"Cannot complete project with status '{self.status.value}'")
    
    def cancel(self) -> None:
        """Отменить проект"""
        if self.status != ProjectStatus.COMPLETED:
            self.status = ProjectStatus.CANCELLED
        else:
            raise ValueError(f"Cannot cancel completed project")
    
    def can_transition_to(self, new_status: ProjectStatus) -> bool:
        """Проверка возможности перехода в новый статус"""
        allowed_transitions = {
            ProjectStatus.DRAFT: [ProjectStatus.ACTIVE, ProjectStatus.CANCELLED],
            ProjectStatus.ACTIVE: [ProjectStatus.SUSPENDED, ProjectStatus.COMPLETED, ProjectStatus.CANCELLED],
            ProjectStatus.SUSPENDED: [ProjectStatus.ACTIVE, ProjectStatus.COMPLETED, ProjectStatus.CANCELLED],
            ProjectStatus.COMPLETED: [],
            ProjectStatus.CANCELLED: [],
        }
        return new_status in allowed_transitions.get(self.status, [])
    
    def __repr__(self):
        return f"<Project(project_id={self.project_id}, project_title='{self.project_title}', status='{self.status.value}')>"
