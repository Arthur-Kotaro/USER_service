# app/services/token_service.py
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from app.config import settings
from app.repositories.refresh_repo import RefreshTokenRepository
from app.repositories.user_repo import UserRepository
from app.utils.hasher import hash_token
from app.utils.redis_client import redis_client


class TokenService:
    def __init__(
        self,
        refresh_repo: RefreshTokenRepository,
        user_repo: UserRepository,
    ):
        self.refresh_repo = refresh_repo
        self.user_repo = user_repo

    @staticmethod
    def _blacklist_key(jti: str) -> str:
        return f"blacklist:{jti}"

    def create_access_token(
        self,
        user_id: int,
        position: Optional[str],
        roles: List[str],
        is_super_admin: bool = False,
    ) -> str:
        payload = {
            "user_id": user_id,
            "position": position,
            "roles": roles,
            "is_super_admin": is_super_admin,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "jti": str(uuid.uuid4()),
            "type": "access",
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    async def create_refresh_token(self, user_id: int) -> str:
        expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "user_id": user_id,
            "exp": expires,
            "jti": str(uuid.uuid4()),
            "type": "refresh",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        token_hash = hash_token(token)
        await self.refresh_repo.create(user_id=user_id, token_hash=token_hash, expires_at=expires)
        return token

    async def decode_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != token_type:
                return None
            if token_type == "access":
                jti = payload.get("jti")
                if jti and await redis_client.exists(self._blacklist_key(jti)):
                    return None
            return payload
        except jwt.PyJWTError:
            return None

    async def revoke_access_token(self, access_token: str) -> bool:
        payload = await self.decode_token(access_token, "access")
        if not payload:
            return False
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        if ttl > 0:
            await redis_client.set(self._blacklist_key(payload["jti"]), "1", ex=ttl)
        return True

    async def revoke_refresh_token(self, refresh_token: str) -> bool:
        token_hash = hash_token(refresh_token)
        return await self.refresh_repo.revoke(token_hash)

    async def revoke_all_user_refresh_tokens(self, user_id: int) -> int:
        return await self.refresh_repo.revoke_all_by_user(user_id)

    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        payload = await self.decode_token(refresh_token, "refresh")
        if not payload:
            return None

        token_hash = hash_token(refresh_token)
        stored = await self.refresh_repo.get_by_hash(token_hash)
        if not stored or stored.revoked or stored.expires_at < datetime.now(timezone.utc):
            return None

        user = await self.user_repo.get_by_id(payload["user_id"])
        if not user:
            return None
        if user.deleted_at is not None:
            return None
        if user.blocked_at is not None:
            if user.block_expires_at is not None:
                if user.block_expires_at > datetime.now(timezone.utc):
                    return None
            else:
                return None

        return self.create_access_token(
            user_id=user.user_id,
            position=user.position.position_code if user.position else None,
            roles=user.get_role_codes(),
            is_super_admin=bool(user.is_super_admin),
        )

    async def is_refresh_token_valid(self, refresh_token: str) -> bool:
        token_hash = hash_token(refresh_token)
        stored = await self.refresh_repo.get_by_hash(token_hash)
        if not stored or stored.revoked:
            return False
        if stored.expires_at < datetime.now(timezone.utc):
            return False
        return True
