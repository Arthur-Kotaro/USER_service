# app/schemas/user.py (ОБНОВЛЕННАЯ ВЕРСИЯ - БЕЗ ПРОЕКТОВ)
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models.user import User


class UserCreate(BaseModel):
    email: EmailStr
    user_name: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=200)
    password: str = Field(..., min_length=12)
    gender: Optional[str] = Field(None, pattern="^[MF]$")
    birth_date: Optional[datetime] = None
    dept_code: Optional[str] = Field(None, max_length=20)
    phone_work: Optional[str] = Field(None, max_length=20)
    phone_mobile: Optional[str] = Field(None, max_length=20)
    head_id: Optional[int] = None
    role_ids: List[int] = []


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    user_name: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=200)
    gender: Optional[str] = Field(None, pattern="^[MF]$")
    birth_date: Optional[datetime] = None
    dept_code: Optional[str] = Field(None, max_length=20)
    phone_work: Optional[str] = Field(None, max_length=20)
    phone_mobile: Optional[str] = Field(None, max_length=20)
    head_id: Optional[int] = None


class UserResponse(BaseModel):
    """Схема для ответа с данными пользователя (без проектов)"""
    user_id: int
    user_name: str
    full_name: Optional[str] = None
    email: Optional[str]
    gender: Optional[str]
    birth_date: Optional[datetime]
    dept_code: Optional[str]
    phone_work: Optional[str]
    phone_mobile: Optional[str]
    head_id: Optional[int] = None
    is_super_admin: bool = False
    status: str
    roles: List[str] = []
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserStatus(str):
    ACTIVE = "active"
    BLOCKED = "blocked"
    LOCKED = "locked"
    DELETED = "deleted"


def get_user_status_from_model(user: User) -> str:
    from datetime import datetime, timezone
    
    if user.deleted_at is not None:
        return "deleted"
    
    if user.blocked_at is not None:
        if user.block_expires_at is not None:
            if user.block_expires_at > datetime.now(timezone.utc):
                return "blocked"
        else:
            return "blocked"
    
    if user.locked_until is not None:
        if user.locked_until > datetime.now(timezone.utc):
            return "locked"
    
    return "active"


def user_to_response(user: User, roles: List[str] = None) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        user_name=user.user_name,
        full_name=user.full_name,
        email=user.email,
        gender=user.gender,
        birth_date=user.birth_date,
        dept_code=user.dept_code,
        phone_work=user.phone_work,
        phone_mobile=user.phone_mobile,
        head_id=user.head_id,
        is_super_admin=user.is_super_admin or False,
        status=get_user_status_from_model(user),
        roles=roles or [],
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )
