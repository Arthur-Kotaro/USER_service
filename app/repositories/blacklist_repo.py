# app/repositories/blacklist_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timezone
from app.models.token_blacklist import TokenBlacklist

class BlacklistRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def add(self, jti: str, expires_at: datetime):
        """Добавить токен в черный список"""
        blacklisted_token = TokenBlacklist(
            token_jti=jti,
            expires_at=expires_at
        )
        self.db.add(blacklisted_token)
        await self.db.commit()
        
    async def is_blacklisted(self, token: str) -> bool:
        """Проверить, находится ли токен в черном списке"""
        result = await self.db.execute(
            select(TokenBlacklist).where(
                TokenBlacklist.token_jti == token,
                TokenBlacklist.expires_at > datetime.now(timezone.utc)
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def delete_expired(self) -> int:
        """Удалить просроченные токены"""
        result = await self.db.execute(
            delete(TokenBlacklist).where(
                TokenBlacklist.expires_at <= datetime.now(timezone.utc)
            )
        )
        await self.db.commit()
        return result.rowcount
