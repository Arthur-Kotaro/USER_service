# app/schemas/admin.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserAdminUpdate(BaseModel):
    """Схема для обновления пользователя администратором"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    
    class Config:
        from_attributes = True

class UserAdminResponse(BaseModel):
    """Схема для ответа с данными пользователя (для админов)"""
    id: int
    email: EmailStr
    username: str
    is_active: bool
    is_admin: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """Схема для списка пользователей с пагинацией"""
    total: int
    users: list[UserAdminResponse]

class AdminStatsResponse(BaseModel):
    """Схема для статистики (админ-панель)"""
    total_users: int
    active_users: int
    inactive_users: int
    admin_users: int
    regular_users: int
