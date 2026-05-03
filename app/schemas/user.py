# app/schemas/user.py - обновленный
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class UserStatus(str, Enum):
    active = "active"
    blocked = "blocked"
    archived = "archived"

class UserCreate(BaseModel):
    """Создание пользователя (только админ)"""
    user_name: str = Field(..., min_length=3, max_length=100)
    password_hash: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None
    gender: Optional[str] = Field(None, pattern="^[MF]$")
    birth_date: Optional[date] = None
    dept_code: Optional[str] = None
    phone_work: Optional[str] = Field(None, max_length=20)
    phone_mobile: Optional[str] = Field(None, max_length=20)
    status: UserStatus = UserStatus.active
    
    @field_validator('gender')
    def validate_gender(cls, v):
        if v and v not in ['M', 'F']:
            raise ValueError('Gender must be M or F')
        return v

class UserUpdate(BaseModel):
    """Обновление пользователя (только админ)"""
    email: Optional[EmailStr] = None
    gender: Optional[str] = Field(None, pattern="^[MF]$")
    birth_date: Optional[date] = None
    dept_code: Optional[str] = None
    phone_work: Optional[str] = Field(None, max_length=20)
    phone_mobile: Optional[str] = Field(None, max_length=20)
    status: Optional[UserStatus] = None

class UserResponse(BaseModel):
    """Ответ с данными пользователя"""
    user_id: int
    user_name: str
    email: Optional[str]
    gender: Optional[str]
    birth_date: Optional[date]
    dept_code: Optional[str]
    phone_work: Optional[str]
    phone_mobile: Optional[str]
    status: str
    created_at: datetime
    last_login_at: Optional[datetime]
    password_updated_at: Optional[datetime]
    roles: List[str] = []
    projects: List[str] = []
    
    class Config:
        from_attributes = True
