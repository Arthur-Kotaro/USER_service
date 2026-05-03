# app/repositories/refresh_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime, timezone
from typing import Optional
from app.models.refresh_token import RefreshToken

class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, token_hash: str, expires_at: datetime) -> RefreshToken:
        token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke(self, token_hash: str):
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked=True)
        )
        await self.db.commit()
    
    async def revoke_all_by_user(self, user_id: int) -> int:
        """Отозвать все refresh токены пользователя"""
        result = await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
            .values(revoked=True)
        )
        await self.db.commit()
        return result.rowcount
    
    async def delete_expired(self) -> int:
        """Удалить просроченные refresh токены"""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            delete(RefreshToken).where(RefreshToken.expires_at <= now)
        )
        await self.db.commit()
        return result.rowcount
