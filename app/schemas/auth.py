# app/schemas/auth.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
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
    requires_password_change: bool = False  # НОВОЕ


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
    password: str = Field(..., min_length=12)  # НОВОЕ: минимум 12 символов
    confirm_password: str = Field(..., min_length=12)

    @field_validator('confirm_password')
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v

    @field_validator('password')
    def validate_password_strength(cls, v):
        import re
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*()\-_=+]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserResponse(BaseModel):
    """Схема для ответа с данными пользователя"""
    id: int
    email: str
    username: str
    full_name: Optional[str] = None  # НОВОЕ
    is_active: bool
    is_admin: bool
    is_super_admin: bool = False  # НОВОЕ
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """Схема для смены пароля"""
    current_password: str
    new_password: str = Field(..., min_length=12)
    confirm_password: str = Field(..., min_length=12)

    @field_validator('confirm_password')
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v

    @field_validator('new_password')
    def validate_password_strength(cls, v):
        import re
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*()\-_=+]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class PasswordExpiryResponse(BaseModel):
    """Схема для ответа с оставшимся временем действия пароля"""
    days_remaining: int
    is_expired: bool
    expires_at: Optional[datetime]


class PasswordResetRequest(BaseModel):
    """Схема для запроса на восстановление доступа"""
    email: EmailStr


class PasswordResetResponse(BaseModel):
    """Схема для ответа на восстановление"""
    message: str
    temp_password_sent: bool
