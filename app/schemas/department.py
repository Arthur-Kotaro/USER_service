# app/schemas/department.py
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class DepartmentResponse(BaseModel):
    dept_id: UUID
    dept_code: str
    dept_name_en: str
    dept_name_ru: str
    parent_dept_id: Optional[UUID]
    type: str
    level: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DepartmentBrief(BaseModel):
    dept_id: UUID
    dept_code: str
    dept_name_ru: str
    type: str
    level: int

    class Config:
        from_attributes = True


class DepartmentTree(BaseModel):
    dept_id: UUID
    dept_code: str
    dept_name_ru: str
    dept_name_en: str
    type: str
    level: int
    children: List["DepartmentTree"] = []

    class Config:
        from_attributes = True
