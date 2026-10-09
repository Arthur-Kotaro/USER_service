# app/api/v1/departments.py
from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.repositories.department_repo import DepartmentRepository
from app.repositories.position_repo import PositionRepository
from app.schemas.department import DepartmentResponse, DepartmentBrief
from app.schemas.position import PositionResponse

router = APIRouter(tags=["Departments & Positions"])


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = DepartmentRepository(db)
    return await repo.get_all()


@router.get("/departments/{dept_code}", response_model=DepartmentResponse)
async def get_department(
    dept_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = DepartmentRepository(db)
    d = await repo.get_by_code(dept_code)
    if not d:
        from fastapi import HTTPException
        raise HTTPException(404, "Department not found")
    return d


@router.get("/positions", response_model=List[PositionResponse])
async def list_positions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = PositionRepository(db)
    return await repo.get_all()
