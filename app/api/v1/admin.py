# app/api/v1/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.dependencies import get_current_admin, get_auth_service
from app.schemas.admin import UserAdminUpdate, UserAdminResponse
from app.services.user_service import UserService
from app.database import get_db
from sqlalchemy.orm import Session

# Создаем роутер
router = APIRouter()

@router.get("/users", response_model=List[UserAdminResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить список всех пользователей (только для админов)"""
    from app.repositories.user_repo import UserRepository
    user_repo = UserRepository(db)
    users = await user_repo.get_all(skip, limit)
    return users

@router.get("/users/{user_id}", response_model=UserAdminResponse)
async def get_user_by_id(
    user_id: int,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить пользователя по ID (только для админов)"""
    from app.repositories.user_repo import UserRepository
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/users/{user_id}", response_model=UserAdminResponse)
async def update_user(
    user_id: int,
    user_data: UserAdminUpdate,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Обновить данные пользователя (только для админов)"""
    from app.repositories.user_repo import UserRepository
    user_repo = UserRepository(db)
    
    # Убираем None значения
    update_dict = {k: v for k, v in user_data.dict().items() if v is not None}
    
    user = await user_repo.update(user_id, update_dict)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Удалить пользователя (только для админов)"""
    from app.repositories.user_repo import UserRepository
    user_repo = UserRepository(db)
    
    deleted = await user_repo.delete(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return None

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Активировать пользователя (только для админов)"""
    from app.repositories.user_repo import UserRepository
    user_repo = UserRepository(db)
    
    user = await user_repo.update(user_id, {"is_active": True})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User activated successfully"}

@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Деактивировать пользователя (только для админов)"""
    from app.repositories.user_repo import UserRepository
    user_repo = UserRepository(db)
    
    user = await user_repo.update(user_id, {"is_active": False})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deactivated successfully"}
