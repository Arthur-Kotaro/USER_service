# app/services/token_service.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from app.config import settings
from app.repositories.blacklist_repo import BlacklistRepository
from app.repositories.refresh_repo import RefreshTokenRepository
from app.repositories.user_repo import UserRepository
from app.utils.hasher import hash_token


class TokenService:
    def __init__(
        self,
        blacklist_repo: BlacklistRepository,
        refresh_repo: RefreshTokenRepository,
        user_repo: UserRepository
    ):
        self.blacklist_repo = blacklist_repo
        self.refresh_repo = refresh_repo
        self.user_repo = user_repo

    def create_access_token(self, user_id: int, projects: List[str], roles: List[str], is_super_admin: bool = False) -> str:
        """Создает access токен с коротким сроком жизни"""
        payload = {
            "user_id": user_id,
            "projects": projects,
            "roles": roles,  # Исправлено: передаём список ролей
            "is_super_admin": is_super_admin,  # НОВОЕ
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "jti": str(uuid.uuid4()),
            "type": "access"
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    async def create_refresh_token(self, user_id: int) -> str:
        """Создает refresh токен и сохраняет его хеш в БД"""
        expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "user_id": user_id,
            "exp": expires,
            "jti": str(uuid.uuid4()),
            "type": "refresh"
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        token_hash = hash_token(token)
        await self.refresh_repo.create(user_id=user_id, token_hash=token_hash, expires_at=expires)
        return token

    async def decode_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Декодирует и проверяет токен (подпись, срок, тип, чёрный список для access)"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != token_type:
                return None

            # Проверка черного списка для access токена
            if token_type == "access":
                is_blacklisted = await self.blacklist_repo.is_blacklisted(payload["jti"])
                if is_blacklisted:
                    return None

            return payload
        except jwt.PyJWTError:
            return None

    async def revoke_access_token(self, access_token: str) -> bool:
        """Добавляет access токен в черный список (при логауте)"""
        payload = await self.decode_token(access_token, "access")
        if payload:
            expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            await self.blacklist_repo.add(jti=payload["jti"], expires_at=expires_at)
            return True
        return False

    async def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Отзыв конкретного refresh токена"""
        token_hash = hash_token(refresh_token)
        return await self.refresh_repo.revoke(token_hash)

    async def revoke_all_user_refresh_tokens(self, user_id: int) -> int:
        """Отозвать все refresh токены пользователя"""
        return await self.refresh_repo.revoke_all_by_user(user_id)

    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Обновляет access токен по refresh токену"""
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

        # Исправлено: используем selectinload
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        query = select(User).options(
            selectinload(User.roles),
            selectinload(User.projects)
        ).where(User.user_id == user.user_id)
        result = await self.user_repo.db.execute(query)
        user = result.unique().scalar_one()

        project_titles = user.get_projects_titles()
        role_titles = user.get_roles_titles()

        new_access = self.create_access_token(
            user_id=user.user_id,
            projects=project_titles,
            roles=role_titles,
            is_super_admin=user.is_super_admin
        )

        return new_access

    async def is_refresh_token_valid(self, refresh_token: str) -> bool:
        """Проверка валидности refresh токена"""
        token_hash = hash_token(refresh_token)
        stored = await self.refresh_repo.get_by_hash(token_hash)

        if not stored or stored.revoked:
            return False

        if stored.expires_at < datetime.now(timezone.utc):
            return False

        return True
