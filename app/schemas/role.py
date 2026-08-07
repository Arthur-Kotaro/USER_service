# app/schemas/role.py (НОВЫЙ ФАЙЛ)
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


# ========== Базовые схемы ==========

class RoleBase(BaseModel):
    """Базовая схема роли"""
    role_title: str = Field(..., min_length=1, max_length=50, description="Англоязычное название роли")
    role_title_ru: Optional[str] = Field(None, max_length=100, description="Русскоязычное название роли")
    role_code: Optional[str] = Field(None, min_length=1, max_length=6, description="Буквенный код (аббревиатура)")
    
    @field_validator('role_code')
    def validate_role_code(cls, v):
        if v is not None:
            if not v.isalnum():
                raise ValueError('Role code must be alphanumeric')
            if len(v) > 6:
                raise ValueError('Role code must be at most 6 characters')
        return v.upper() if v else v


# ========== Схемы для создания и обновления ==========

class RoleCreate(RoleBase):
    """Схема для создания роли"""
    pass


class RoleUpdate(BaseModel):
    """Схема для обновления роли"""
    role_title: Optional[str] = Field(None, min_length=1, max_length=50)
    role_title_ru: Optional[str] = Field(None, max_length=100)
    role_code: Optional[str] = Field(None, min_length=1, max_length=6)
    
    @field_validator('role_code')
    def validate_role_code(cls, v):
        if v is not None:
            if not v.isalnum():
                raise ValueError('Role code must be alphanumeric')
            if len(v) > 6:
                raise ValueError('Role code must be at most 6 characters')
        return v.upper() if v else v


# ========== Схемы для ответа ==========

class RoleResponse(RoleBase):
    """Схема ответа с данными роли"""
    role_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RoleBriefResponse(BaseModel):
    """Краткая схема ответа (для списков)"""
    role_id: int
    role_title: str
    role_title_ru: Optional[str]
    role_code: Optional[str]
    
    class Config:
        from_attributes = True
    
    @property
    def display_name(self) -> str:
        """Отображаемое название (русское если есть, иначе английское)"""
        return self.role_title_ru or self.role_title


# ========== Схемы для назначения ролей пользователю ==========

class AssignRoleRequest(BaseModel):
    """Схема для назначения роли пользователю"""
    role_id: int = Field(..., gt=0, description="ID роли")
    
    @field_validator('role_id')
    def validate_role_id(cls, v):
        if v <= 0:
            raise ValueError('role_id must be positive')
        return v


class AssignRoleByCodeRequest(BaseModel):
    """Схема для назначения роли по коду"""
    role_code: str = Field(..., min_length=1, max_length=6, description="Буквенный код роли")
    
    @field_validator('role_code')
    def validate_role_code(cls, v):
        if not v.isalnum():
            raise ValueError('Role code must be alphanumeric')
        return v.upper()


class UserRoleResponse(BaseModel):
    """Схема ответа с ролями пользователя"""
    user_id: int
    roles: List[RoleBriefResponse] = []
    
    class Config:
        from_attributes = True


# ========== Вспомогательные функции ==========

def role_to_response(role) -> RoleResponse:
    """Преобразование модели Role в RoleResponse"""
    return RoleResponse(
        role_id=role.role_id,
        role_title=role.role_title,
        role_title_ru=role.role_title_ru,
        role_code=role.role_code,
    )


def role_to_brief(role) -> RoleBriefResponse:
    """Преобразование модели Role в RoleBriefResponse"""
    return RoleBriefResponse(
        role_id=role.role_id,
        role_title=role.role_title,
        role_title_ru=role.role_title_ru,
        role_code=role.role_code,
    )
