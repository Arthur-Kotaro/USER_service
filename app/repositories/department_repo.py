# app/repositories/department_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.models.department import Department


class DepartmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, dept_id) -> Optional[Department]:
        result = await self.db.execute(
            select(Department).where(Department.dept_id == dept_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, dept_code: str) -> Optional[Department]:
        result = await self.db.execute(
            select(Department).where(Department.dept_code == dept_code)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 500) -> List[Department]:
        result = await self.db.execute(
            select(Department).order_by(Department.level, Department.dept_code).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_children(self, parent_dept_id) -> List[Department]:
        result = await self.db.execute(
            select(Department).where(Department.parent_dept_id == parent_dept_id).order_by(Department.dept_code)
        )
        return result.scalars().all()

    async def get_by_level(self, level: int) -> List[Department]:
        result = await self.db.execute(
            select(Department).where(Department.level == level).order_by(Department.dept_code)
        )
        return result.scalars().all()
