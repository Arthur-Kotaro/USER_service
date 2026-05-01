# app/repositories/blacklist_repo.py
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.token_blacklist import TokenBlacklist

class BlacklistRepository:
    def __init__(self, db: Session):
        self.db = db
    
    async def add_token(self, token: str, expires_at: datetime):
        """Добавить токен в черный список"""
        blacklisted_token = TokenBlacklist(
            token=token,
            expires_at=expires_at
        )
        self.db.add(blacklisted_token)
        await self.db.commit()
        
    async def is_blacklisted(self, token: str) -> bool:
        """Проверить, находится ли токен в черном списке"""
        return self.db.query(TokenBlacklist).filter(
            TokenBlacklist.token == token,
            TokenBlacklist.expires_at > datetime.utcnow()
        ).first() is not None
    
    async def delete_expired(self) -> int:
        """Удалить просроченные токены"""
        deleted = self.db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at <= datetime.utcnow()
        ).delete()
        self.db.commit()
        return deleted
