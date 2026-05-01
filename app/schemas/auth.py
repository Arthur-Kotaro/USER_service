# app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    """Схема для запроса на вход"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Схема для ответа с токенами"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Схема для данных токена"""
    user_id: int
    email: str
    is_admin: bool = False

class RefreshTokenRequest(BaseModel):
    """Схема для обновления токена"""
    refresh_token: str

class RegisterRequest(BaseModel):
    """Схема для регистрации пользователя"""
    email: EmailStr
    username: str
    password: str
    confirm_password: str

class UserResponse(BaseModel):
    """Схема для ответа с данными пользователя"""
    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Для работы с SQLAlchemy моделями (Pydantic v2)
        # или или orm_mode = True (для Pydantic v1)
