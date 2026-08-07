# app/schemas/user.py (ОБНОВЛЁННАЯ ВЕРСИЯ)
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

# ВНИМАНИЕ: UserStatus больше не хранится в БД, оставлен для обратной совместимости API
class UserStatus(str, Enum):
    active = "active"
    blocked = "blocked"
    archived = "archived"
    deleted = "deleted"  # Добавлен статус для soft delete


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
    # status УДАЛЁН - пользователь создаётся активным (не заблокированным)
    
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
    # status УДАЛЁН - используйте отдельные эндпоинты для блокировки/разблокировки


class UserBlock(BaseModel):
    """Блокировка пользователя"""
    reason: str = Field(..., min_length=1, max_length=500)
    expires_at: Optional[datetime] = None  # NULL = бессрочно


class UserUnblock(BaseModel):
    """Разблокировка пользователя"""
    reason: Optional[str] = Field(None, max_length=500)


class UserSoftDelete(BaseModel):
    """Мягкое удаление пользователя"""
    reason: Optional[str] = Field(None, max_length=500)


class UserRestore(BaseModel):
    """Восстановление пользователя"""
    reason: Optional[str] = Field(None, max_length=500)


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
    
    # Статус (вычисляется из blocked_at и deleted_at)
    status: str  # 'active', 'blocked', 'deleted'
    
    # Информация о блокировке
    blocked_at: Optional[datetime]
    blocked_reason: Optional[str]
    block_expires_at: Optional[datetime]
    
    # Информация об удалении (soft delete)
    deleted_at: Optional[datetime]
    
    # Аудит
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    password_updated_at: Optional[datetime]
    
    # Связи
    roles: List[str] = []
    projects: List[str] = []
    
    class Config:
        from_attributes = True


class UserBriefResponse(BaseModel):
    """Краткий ответ с данными пользователя (для списков)"""
    user_id: int
    user_name: str
    email: Optional[str]
    status: str
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserStatusResponse(BaseModel):
    """Ответ о статусе пользователя"""
    user_id: int
    user_name: str
    is_active: bool      # Не заблокирован и не удалён
    is_blocked: bool     # Заблокирован
    is_deleted: bool     # Удалён (soft delete)
    blocked_reason: Optional[str]
    block_expires_at: Optional[datetime]
    deleted_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserBlockHistoryResponse(BaseModel):
    """История блокировок пользователя (из audit_log)"""
    blocked_at: datetime
    blocked_reason: Optional[str]
    blocked_by: Optional[int]
    blocked_by_name: Optional[str]
    block_expires_at: Optional[datetime]
    unblocked_at: Optional[datetime]
    unblocked_by: Optional[int]
    unblocked_by_name: Optional[str]


# ============= Вспомогательные функции для преобразования =============

def get_user_status_from_model(user) -> str:
    """
    Определяет статус пользователя на основе полей модели
    """
    if user.deleted_at is not None:
        return "deleted"
    if user.blocked_at is not None:
        # Проверяем, не истекла ли временная блокировка
        if user.block_expires_at is not None:
            from datetime import datetime, timezone
            if user.block_expires_at <= datetime.now(timezone.utc):
                return "active"  # Блокировка истекла
        return "blocked"
    return "active"


def user_to_response(user, roles: List[str] = None, projects: List[str] = None) -> UserResponse:
    """
    Преобразует модель User в UserResponse
    """
    return UserResponse(
        user_id=user.user_id,
        user_name=user.user_name,
        email=user.email,
        gender=user.gender,
        birth_date=user.birth_date,
        dept_code=user.dept_code,
        phone_work=user.phone_work,
        phone_mobile=user.phone_mobile,
        status=get_user_status_from_model(user),
        blocked_at=user.blocked_at,
        blocked_reason=user.blocked_reason,
        block_expires_at=user.block_expires_at,
        deleted_at=user.deleted_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
        password_updated_at=user.password_updated_at,
        roles=roles or [],
        projects=projects or [],
    )
