# app/api/v1/projects.py (НОВЫЙ ФАЙЛ)
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.project import (
    ProjectResponse, ProjectCreate, ProjectUpdate, 
    ProjectStatusUpdate, ProjectBriefResponse,
    project_to_response, can_transition_to
)
from app.models.user import User

router = APIRouter(prefix="/projects", tags=["Projects"])


# ========== Вспомогательные функции ==========

async def get_project_repository(db):
    """Репозиторий для работы с проектами"""
    from app.repositories.project_repo import ProjectRepository
    return ProjectRepository(db)


# ========== CRUD проектов ==========

@router.get("/", response_model=List[ProjectBriefResponse])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Получение списка проектов
    """
    project_repo = await get_project_repository(db)
    projects = await project_repo.get_all(skip, limit, status=status)
    return [project_to_brief(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Получение информации о проекте по ID
    """
    project_repo = await get_project_repository(db)
    project = await project_repo.get_by_id(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project_to_response(project)


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Создание нового проекта
    """
    project_repo = await get_project_repository(db)
    
    # Проверка на существование проекта с таким названием
    existing = await project_repo.get_by_title(project_data.project_title)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project with this title already exists"
        )
    
    project = await project_repo.create(
        title=project_data.project_title,
        description=project_data.project_description,
        status=project_data.status
    )
    
    return project_to_response(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Обновление информации о проекте
    """
    project_repo = await get_project_repository(db)
    
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    update_dict = project_data.model_dump(exclude_unset=True)
    project = await project_repo.update(project_id, update_dict)
    
    return project_to_response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Удаление проекта
    """
    project_repo = await get_project_repository(db)
    
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    deleted = await project_repo.delete(project_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )
    
    return None


# ========== Управление статусом проекта ==========

@router.patch("/{project_id}/status", response_model=ProjectResponse)
async def update_project_status(
    project_id: int,
    status_data: ProjectStatusUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Обновление статуса проекта
    """
    project_repo = await get_project_repository(db)
    
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Проверка возможности перехода
    if not can_transition_to(project.status, status_data.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {project.status.value} to {status_data.status.value}"
        )
    
    project = await project_repo.update_status(project_id, status_data.status)
    
    return project_to_response(project)


@router.get("/{project_id}/status")
async def get_project_status(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Получение статуса проекта
    """
    project_repo = await get_project_repository(db)
    
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return {
        "project_id": project_id,
        "project_title": project.project_title,
        "status": project.status.value,
        "status_display": {
            "draft": "Черновик",
            "active": "Активен",
            "suspended": "Приостановлен",
            "completed": "Завершён",
            "cancelled": "Отменён"
        }.get(project.status.value, project.status.value)
    }


# ========== Участники проекта ==========

@router.get("/{project_id}/users")
async def get_project_users(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Получение списка участников проекта
    """
    project_repo = await get_project_repository(db)
    
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    users = await project_repo.get_users(project_id)
    
    return {
        "project_id": project_id,
        "project_title": project.project_title,
        "users": [
            {
                "user_id": user.user_id,
                "user_name": user.user_name,
                "email": user.email
            }
            for user in users
        ]
    }


@router.post("/{project_id}/users/{user_id}")
async def add_user_to_project(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Добавление пользователя в проект
    """
    project_repo = await get_project_repository(db)
    
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    success = await project_repo.add_user(project_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add user to project (user may not exist or already in project)"
        )
    
    return {"message": "User added to project successfully"}


@router.delete("/{project_id}/users/{user_id}")
async def remove_user_from_project(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Удаление пользователя из проекта
    """
    project_repo = await get_project_repository(db)
    
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    success = await project_repo.remove_user(project_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove user from project"
        )
    
    return {"message": "User removed from project successfully"}
