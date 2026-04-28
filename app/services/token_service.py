import jwt
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from app.config import settings
from app.repositories import BlacklistRepository, RefreshTokenRepository
from app.utils.hasher import hash_token  # sha256 хеш

class TokenService:
    def __init__(self, blacklist_repo: BlacklistRepository, refresh_repo: RefreshTokenRepository):
        self.blacklist_repo = blacklist_repo
        self.refresh_repo = refresh_repo

    def create_access_token(self, user_id: int, projects: List[str], role: str) -> str:
        """Создает access токен с коротким сроком жизни"""
        payload = {
            "user_id": user_id,
            "projects": projects,
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "jti": str(uuid.uuid4()),   # уникальный ID токена
            "type": "access"
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def create_refresh_token(self, user_id: int) -> str:
        """Создает refresh токен и сохраняет его хеш в БД"""
        expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "user_id": user_id,
            "exp": expires,
            "jti": str(uuid.uuid4()),
            "type": "refresh"
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        # Храним хеш refresh токена (а не сам токен) для защиты от утечки БД
        token_hash = hash_token(token)
        # Сохраняем в БД
        self.refresh_repo.create(user_id=user_id, token_hash=token_hash, expires_at=expires)
        return token

    def decode_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Декодирует и проверяет токен (подпись, срок, тип, чёрный список для access)"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != token_type:
                return None
            # Проверка черного списка для access токена
            if token_type == "access":
                if self.blacklist_repo.is_blacklisted(payload["jti"]):
                    return None
            return payload
        except jwt.PyJWTError:
            return None

    def revoke_access_token(self, access_token: str):
        """Добавляет access токен в черный список (при логауте)"""
        payload = self.decode_token(access_token, "access")
        if payload:
            self.blacklist_repo.add(jti=payload["jti"], expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc))

    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Обновляет access токен по refresh токену"""
        payload = self.decode_token(refresh_token, "refresh")
        if not payload:
            return None
        # Проверяем, что refresh токен не отозван и существует в БД
        token_hash = hash_token(refresh_token)
        stored = await self.refresh_repo.get_by_hash(token_hash)
        if not stored or stored.revoked or stored.expires_at < datetime.now(timezone.utc):
            return None
        # Получаем пользователя из БД для актуальных проектов и роли
        user = await self.user_repo.get_by_id(payload["user_id"])  # нужно внедрить репозиторий пользователей
        if not user or not user.is_active:
            return None
        projects = json.loads(user.projects)  # из модели
        new_access = self.create_access_token(user.id, projects, user.role)
        return new_access
