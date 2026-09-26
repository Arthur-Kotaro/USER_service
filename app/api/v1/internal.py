# app/api/v1/internal.py
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, user_to_response
from app.config import settings

router = APIRouter(tags=["Internal"])

async def verify_internal_key(x_internal_key: str = Header(...)):
    """Проверка внутреннего ключа доступа"""
    if x_internal_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid internal key")
    return True

@router.get("/users", response_model=List[UserResponse])
async def get_users_internal(
    search: Optional[str] = Query(None, min_length=2),
    limit: int = Query(50, ge=1, le=200),
    _: bool = Depends(verify_internal_key),
    db = Depends(get_db)
):
    """
    Внутренний эндпоинт для UI Composer.
    Возвращает список пользователей с фильтрацией по поиску.
    """
    stmt = select(User).options(
        selectinload(User.roles),
        selectinload(User.department)
    ).where(User.deleted_at.is_(None))
    
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                User.full_name.ilike(search_pattern),
                User.user_name.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        )
    
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    users = result.unique().scalars().all()
    
    return [user_to_response(u, u.get_roles_titles()) for u in users]

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_internal(
    user_id: int,
    _: bool = Depends(verify_internal_key),
    db = Depends(get_db)
):
    """
    Внутренний эндпоинт для UI Composer.
    Возвращает данные пользователя по ID.
    """
    stmt = select(User).options(
        selectinload(User.roles),
        selectinload(User.department)
    ).where(
        User.user_id == user_id,
        User.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    user = result.unique().scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user_to_response(user, user.get_roles_titles())
