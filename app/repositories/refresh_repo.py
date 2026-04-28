from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.refresh_token import RefreshToken

class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, token_hash: str, expires_at: datetime) -> RefreshToken:
        token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.session.add(token)
        await self.session.commit()
        return token

    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        result = await self.session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        return result.scalar_one_or_none()

    async def revoke(self, token_hash: str):
        await self.session.execute(update(RefreshToken).where(RefreshToken.token_hash == token_hash).values(revoked=True))
        await self.session.commit()
