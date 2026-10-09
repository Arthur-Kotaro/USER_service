# app/repositories/position_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.models.position import Position


class PositionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, position_id: int) -> Optional[Position]:
        result = await self.db.execute(
            select(Position).where(Position.position_id == position_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, position_code: str) -> Optional[Position]:
        result = await self.db.execute(
            select(Position).where(Position.position_code == position_code)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Position]:
        result = await self.db.execute(
            select(Position).order_by(Position.position_code)
        )
        return result.scalars().all()
