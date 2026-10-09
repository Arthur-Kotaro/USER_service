# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID


class UserCreate(BaseModel):
    email: EmailStr
    user_name: str = Field(..., min_length=3, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    password: str = Field(..., min_length=12)
    gender: Optional[str] = Field(None, pattern="^[MF]$")
    birth_date: Optional[date] = None
    position_id: int
    dept_id: Optional[UUID] = None
    phone_work: Optional[str] = Field(None, max_length=20)
    phone_mobile: Optional[str] = Field(None, max_length=20)
    role_ids: List[int] = []


class UserUpdate(BaseModel):
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, pattern="^[MF]$")
    birth_date: Optional[date] = None
    phone_work: Optional[str] = Field(None, max_length=20)
    phone_mobile: Optional[str] = Field(None, max_length=20)


class UserAdminUpdate(BaseModel):
    email: Optional[EmailStr] = None
    user_name: Optional[str] = Field(None, min_length=3, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, pattern="^[MF]$")
    birth_date: Optional[date] = None
    position_id: Optional[int] = None
    dept_id: Optional[UUID] = None
    phone_work: Optional[str] = Field(None, max_length=20)
    phone_mobile: Optional[str] = Field(None, max_length=20)


class UserResponse(BaseModel):
    user_id: int
    user_name: str
    last_name: str
    first_name: str
    middle_name: Optional[str]
    full_name: str
    email: Optional[str]
    gender: Optional[str]
    birth_date: Optional[date]
    position_id: int
    position_code: Optional[str] = None
    position_name_ru: Optional[str] = None
    dept_id: Optional[UUID]
    dept_code: Optional[str] = None
    dept_name_ru: Optional[str] = None
    phone_work: Optional[str]
    phone_mobile: Optional[str]
    is_super_admin: bool = False
    status: str
    roles: List[str] = []
    role_codes: List[str] = []
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserStatus:
    ACTIVE = "active"
    BLOCKED = "blocked"
    LOCKED = "locked"
    DELETED = "deleted"


def get_user_status_from_model(user) -> str:
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


def user_to_response(user) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        user_name=user.user_name,
        last_name=user.last_name,
        first_name=user.first_name,
        middle_name=user.middle_name,
        full_name=user.full_name,
        email=user.email,
        gender=user.gender,
        birth_date=user.birth_date,
        position_id=user.position_id,
        position_code=user.position.position_code if user.position else None,
        position_name_ru=user.position.position_name_ru if user.position else None,
        dept_id=user.dept_id,
        dept_code=user.department.dept_code if user.department else None,
        dept_name_ru=user.department.dept_name_ru if user.department else None,
        phone_work=user.phone_work,
        phone_mobile=user.phone_mobile,
        is_super_admin=bool(user.is_super_admin),
        status=get_user_status_from_model(user),
        roles=user.get_role_titles(),
        role_codes=user.get_role_codes(),
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )
