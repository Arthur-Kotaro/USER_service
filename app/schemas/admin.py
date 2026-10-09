# app/schemas/admin.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.schemas.user import UserAdminUpdate, UserStatus


class UserAdminResponse(BaseModel):
    user_id: int
    user_name: str
    last_name: str
    first_name: str
    middle_name: Optional[str]
    full_name: str
    email: Optional[str]
    gender: Optional[str]
    birth_date: Optional[datetime]
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
    is_blocked: bool
    is_locked: bool = False
    is_deleted: bool
    blocked_reason: Optional[str]
    blocked_at: Optional[datetime]
    block_expires_at: Optional[datetime]
    locked_until: Optional[datetime] = None
    deleted_at: Optional[datetime]

    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    password_updated_at: Optional[datetime]

    roles: List[str] = []
    role_codes: List[str] = []

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    total: int
    users: List[UserAdminResponse]


def user_to_admin_response(user) -> UserAdminResponse:
    from app.schemas.user import get_user_status_from_model
    from datetime import datetime, timezone
    is_locked = False
    if user.locked_until is not None:
        is_locked = user.locked_until > datetime.now(timezone.utc)

    return UserAdminResponse(
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
        is_blocked=user.blocked_at is not None,
        is_locked=is_locked,
        is_deleted=user.deleted_at is not None,
        blocked_reason=user.blocked_reason,
        blocked_at=user.blocked_at,
        block_expires_at=user.block_expires_at,
        locked_until=user.locked_until,
        deleted_at=user.deleted_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
        password_updated_at=user.password_updated_at,
        roles=user.get_role_titles(),
        role_codes=user.get_role_codes(),
    )
