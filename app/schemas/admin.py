# app/schemas/admin.py (ОБНОВЛЁННАЯ ВЕРСИЯ)
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.user import UserStatus


# ========== Схемы для обновления пользователя (админ) ==========

class UserAdminUpdate(BaseModel):
    """Схема для обновления пользователя администратором"""
    email: Optional[EmailStr] = None
    user_name: Optional[str] = Field(None, min_length=3, max_length=100)
    gender: Optional[str] = Field(None, pattern="^[MF]$")
    birth_date: Optional[datetime] = None
    dept_code: Optional[str] = Field(None, max_length=20)
    phone_work: Optional[str] = Field(None, max_length=20)
    phone_mobile: Optional[str] = Field(None, max_length=20)
    
    # Поля для управления статусом
    block_reason: Optional[str] = Field(None, max_length=500)
    block_expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ========== Схемы для ответа (админ) ==========

class UserAdminResponse(BaseModel):
    """Схема для ответа с данными пользователя (для админов)"""
    user_id: int
    user_name: str
    email: Optional[str]
    gender: Optional[str]
    birth_date: Optional[datetime]
    dept_code: Optional[str]
    phone_work: Optional[str]
    phone_mobile: Optional[str]
    
    # Статус
    status: str  # active, blocked, deleted
    is_blocked: bool
    is_deleted: bool
    blocked_reason: Optional[str]
    blocked_at: Optional[datetime]
    block_expires_at: Optional[datetime]
    deleted_at: Optional[datetime]
    
    # Аудит
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    password_updated_at: Optional[datetime]
    
    # Роли и проекты
    roles: List[str] = []
    projects: List[str] = []
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Схема для списка пользователей с пагинацией"""
    total: int
    users: List[UserAdminResponse]


# ========== Схемы для блокировки ==========

class BlockUserRequest(BaseModel):
    """Схема для блокировки пользователя"""
    reason: str = Field(..., min_length=1, max_length=500, description="Причина блокировки")
    expires_at: Optional[datetime] = Field(None, description="Дата истечения блокировки (NULL = бессрочно)")


class UnblockUserRequest(BaseModel):
    """Схема для разблокировки пользователя"""
    reason: Optional[str] = Field(None, max_length=500, description="Причина разблокировки")


class BlockUserResponse(BaseModel):
    """Схема ответа после блокировки"""
    user_id: int
    user_name: str
    blocked_at: datetime
    blocked_reason: str
    block_expires_at: Optional[datetime]
    blocked_by: int
    blocked_by_name: Optional[str]


# ========== Схемы для soft delete ==========

class SoftDeleteUserRequest(BaseModel):
    """Схема для мягкого удаления пользователя"""
    reason: Optional[str] = Field(None, max_length=500, description="Причина удаления")


class RestoreUserRequest(BaseModel):
    """Схема для восстановления пользователя"""
    reason: Optional[str] = Field(None, max_length=500, description="Причина восстановления")


class DeletedUserResponse(BaseModel):
    """Схема ответа для удалённого пользователя"""
    user_id: int
    user_name: str
    email: Optional[str]
    deleted_at: datetime
    deleted_reason: Optional[str]
    deleted_by: Optional[int]
    deleted_by_name: Optional[str]


# ========== Схемы для статистики ==========

class AdminStatsResponse(BaseModel):
    """Схема для статистики (админ-панель)"""
    total_users: int
    active_users: int          # не заблокированы и не удалены
    blocked_users: int         # заблокированы (включая временно)
    deleted_users: int         # мягко удалены
    admin_users: int           # пользователи с ролью admin
    regular_users: int         # обычные пользователи
    users_with_temp_password: int
    users_password_expiring_soon: int  # пароль истекает через < 7 дней


# ========== Схемы для истории блокировок ==========

class BlockHistoryResponse(BaseModel):
    """Схема истории блокировок пользователя"""
    blocked_at: datetime
    blocked_reason: Optional[str]
    blocked_by: int
    blocked_by_name: Optional[str]
    block_expires_at: Optional[datetime]
    unblocked_at: Optional[datetime]
    unblocked_by: Optional[int]
    unblocked_by_name: Optional[str]


# ========== Вспомогательные функции ==========

def user_to_admin_response(user, roles: List[str] = None, projects: List[str] = None) -> UserAdminResponse:
    """Преобразование модели User в UserAdminResponse"""
    from app.schemas.user import get_user_status_from_model
    
    return UserAdminResponse(
        user_id=user.user_id,
        user_name=user.user_name,
        email=user.email,
        gender=user.gender,
        birth_date=user.birth_date,
        dept_code=user.dept_code,
        phone_work=user.phone_work,
        phone_mobile=user.phone_mobile,
        status=get_user_status_from_model(user),
        is_blocked=user.blocked_at is not None,
        is_deleted=user.deleted_at is not None,
        blocked_reason=user.blocked_reason,
        blocked_at=user.blocked_at,
        block_expires_at=user.block_expires_at,
        deleted_at=user.deleted_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
        password_updated_at=user.password_updated_at,
        roles=roles or [],
        projects=projects or [],
    )
