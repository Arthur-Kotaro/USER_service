# app/schemas/role.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RoleResponse(BaseModel):
    role_id: int
    role_code: str
    role_name_en: str
    role_name_ru: str
    created_at: datetime

    class Config:
        from_attributes = True


class RoleBrief(BaseModel):
    role_id: int
    role_code: str
    role_name_ru: str

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    role_code: str = Field(..., min_length=1, max_length=50)
    role_name_en: str = Field(..., min_length=1, max_length=100)
    role_name_ru: str = Field(..., min_length=1, max_length=100)


class AssignRoleRequest(BaseModel):
    role_id: int = Field(..., gt=0)


class UserRolesResponse(BaseModel):
    user_id: int
    roles: List[RoleBrief] = []
