# app/schemas/project.py (НОВЫЙ ФАЙЛ)
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ========== Enum для статусов ==========

class ProjectStatus(str, Enum):
    """Статусы проекта"""
    DRAFT = "draft"          # создан (черновик)
    ACTIVE = "active"        # активен
    SUSPENDED = "suspended"  # приостановлен
    COMPLETED = "completed"  # завершён
    CANCELLED = "cancelled"  # отменён


# ========== Базовые схемы ==========

class ProjectBase(BaseModel):
    """Базовая схема проекта"""
    project_title: str = Field(..., min_length=1, max_length=100, description="Название проекта")
    project_description: Optional[str] = Field(None, description="Описание проекта")
    
    @field_validator('project_title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Project title cannot be empty')
        return v.strip()


# ========== Схемы для создания и обновления ==========

class ProjectCreate(ProjectBase):
    """Схема для создания проекта"""
    status: Optional[ProjectStatus] = Field(default=ProjectStatus.DRAFT, description="Статус проекта")


class ProjectUpdate(BaseModel):
    """Схема для обновления проекта"""
    project_title: Optional[str] = Field(None, min_length=1, max_length=100)
    project_description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    
    @field_validator('project_title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Project title cannot be empty')
        return v.strip() if v else v


class ProjectStatusUpdate(BaseModel):
    """Схема для обновления только статуса проекта"""
    status: ProjectStatus = Field(..., description="Новый статус проекта")
    
    @field_validator('status')
    def validate_status_transition(cls, v, info):
        # Базовая валидация, полная логика будет в сервисе
        return v


# ========== Схемы для ответа ==========

class ProjectResponse(ProjectBase):
    """Схема ответа с данными проекта"""
    project_id: int
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectBriefResponse(BaseModel):
    """Краткая схема ответа (для списков)"""
    project_id: int
    project_title: str
    status: ProjectStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProjectWithUsersResponse(ProjectResponse):
    """Схема ответа с участниками проекта"""
    user_ids: List[int] = []
    user_names: List[str] = []
    
    class Config:
        from_attributes = True


# ========== Схемы для назначения пользователей ==========

class AddUserToProjectRequest(BaseModel):
    """Схема для добавления пользователя в проект"""
    user_id: int = Field(..., gt=0, description="ID пользователя")
    project_role: str = Field(default="member", pattern="^(owner|member|guest)$", description="Роль в проекте")


class RemoveUserFromProjectRequest(BaseModel):
    """Схема для удаления пользователя из проекта"""
    user_id: int = Field(..., gt=0, description="ID пользователя")


# ========== Вспомогательные функции ==========

def project_to_response(project) -> ProjectResponse:
    """Преобразование модели Project в ProjectResponse"""
    return ProjectResponse(
        project_id=project.project_id,
        project_title=project.project_title,
        project_description=project.project_description,
        status=ProjectStatus(project.status.value if hasattr(project.status, 'value') else project.status),
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def project_to_brief(project) -> ProjectBriefResponse:
    """Преобразование модели Project в ProjectBriefResponse"""
    return ProjectBriefResponse(
        project_id=project.project_id,
        project_title=project.project_title,
        status=ProjectStatus(project.status.value if hasattr(project.status, 'value') else project.status),
        created_at=project.created_at,
    )


def get_allowed_status_transitions() -> dict:
    """Возвращает разрешённые переходы статусов"""
    return {
        ProjectStatus.DRAFT: [ProjectStatus.ACTIVE, ProjectStatus.CANCELLED],
        ProjectStatus.ACTIVE: [ProjectStatus.SUSPENDED, ProjectStatus.COMPLETED, ProjectStatus.CANCELLED],
        ProjectStatus.SUSPENDED: [ProjectStatus.ACTIVE, ProjectStatus.COMPLETED, ProjectStatus.CANCELLED],
        ProjectStatus.COMPLETED: [],
        ProjectStatus.CANCELLED: [],
    }


def can_transition_to(current_status: ProjectStatus, new_status: ProjectStatus) -> bool:
    """Проверка возможности перехода в новый статус"""
    allowed = get_allowed_status_transitions()
    return new_status in allowed.get(current_status, [])
