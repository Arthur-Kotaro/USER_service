# app/api/v1/navigation.py (ТОЛЬКО МЕНЮ, БЕЗ ПЛИТОК)
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.dependencies import get_current_user
from app.models.user import User
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/navigation", tags=["Navigation"])

class MenuItem(BaseModel):
    id: str
    label: str
    endpoint: str
    method: str = "GET"
    requires_project: bool = False
    roles_required: List[str] = []
    section: Optional[str] = None
    icon: Optional[str] = None

class MenuSection(BaseModel):
    section: str
    icon: Optional[str] = None
    items: List[MenuItem]

class NavigationResponse(BaseModel):
    user: dict
    menu: List[MenuSection]

# Только статическое меню
MENU_CONFIG = {
    "admin": [
        {
            "section": "Администрирование",
            "icon": "shield",
            "items": [
                {"id": "users_manage", "label": "Управление пользователями", "endpoint": "/api/v1/admin/users", "method": "GET"},
                {"id": "users_create", "label": "Создать пользователя", "endpoint": "/api/v1/admin/users", "method": "POST"}
            ]
        }
    ]
}

@router.get("/menu", response_model=NavigationResponse)
async def get_menu(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(User).options(
        selectinload(User.roles),
        selectinload(User.projects)
    ).where(User.user_id == current_user.user_id)
    result = await db.execute(query)
    user = result.unique().scalar_one()
    
    role_titles = [r.role_title for r in user.roles] if user.roles else []
    is_super_admin = user.is_super_admin
    
    menu = []
    if is_super_admin:
        menu = MENU_CONFIG["admin"]
    
    return NavigationResponse(
        user={
            "id": user.user_id,
            "user_name": user.user_name,
            "full_name": user.full_name,
            "email": user.email,
            "roles": role_titles,
            "is_super_admin": is_super_admin
        },
        menu=menu
    )
