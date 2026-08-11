# app/dependencies.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.services.token_service import TokenService
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.services.user_service import UserService
from app.services.admin_service import AdminService
from app.repositories.user_repo import UserRepository
from app.repositories.blacklist_repo import BlacklistRepository
from app.repositories.refresh_repo import RefreshTokenRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.login_history_repo import LoginHistoryRepository
from app.repositories.project_repo import ProjectRepository
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Получить текущего пользователя из JWT токена"""
    token = credentials.credentials

    blacklist_repo = BlacklistRepository(db)
    refresh_repo = RefreshTokenRepository(db)
    user_repo = UserRepository(db)
    token_service = TokenService(blacklist_repo, refresh_repo, user_repo)

    # ИСПРАВЛЕНО: добавлен await
    payload = await token_service.decode_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ИСПРАВЛЕНО: используем selectinload
    query = select(User).options(
        selectinload(User.roles),
        selectinload(User.projects),
        selectinload(User.department)
    ).where(User.user_id == payload.get("user_id"))
    result = await db.execute(query)
    user = result.unique().scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deleted"
        )

    # Проверка блокировки (с учетом временной блокировки)
    if user.blocked_at is not None:
        if user.block_expires_at is not None:
            from datetime import datetime, timezone
            if user.block_expires_at > datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account is blocked: {user.blocked_reason or 'No reason provided'}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is blocked: {user.blocked_reason or 'No reason provided'}"
            )

    # НОВОЕ: Проверка временной блокировки (locked_until)
    if user.locked_until is not None:
        from datetime import datetime, timezone
        if user.locked_until > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account temporarily locked until {user.locked_until.isoformat()}"
            )

    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Получить текущего администратора (проверка роли admin)"""
    # НОВОЕ: Проверка супер-админа
    if current_user.is_super_admin:
        return current_user

    roles = current_user.get_roles_titles()
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def get_current_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Получить текущего супер-админа"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    return current_user


async def get_current_user_with_optional_roles(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Получить текущего пользователя из JWT токена (без проверки блокировки/удаления).
    Используется для эндпоинтов, где нужен пользователь, но блокировка не должна мешать
    (например, для проверки статуса блокировки)
    """
    token = credentials.credentials

    blacklist_repo = BlacklistRepository(db)
    refresh_repo = RefreshTokenRepository(db)
    user_repo = UserRepository(db)
    token_service = TokenService(blacklist_repo, refresh_repo, user_repo)

    # ИСПРАВЛЕНО: добавлен await
    payload = await token_service.decode_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    query = select(User).options(
        selectinload(User.roles),
        selectinload(User.projects)
    ).where(User.user_id == payload.get("user_id"))
    result = await db.execute(query)
    user = result.unique().scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


# ========== Сервисы ==========

async def get_auth_service(db: AsyncSession = Depends(get_db)):
    """Dependency для AuthService"""
    user_repo = UserRepository(db)
    blacklist_repo = BlacklistRepository(db)
    refresh_repo = RefreshTokenRepository(db)
    token_service = TokenService(blacklist_repo, refresh_repo, user_repo)
    email_service = EmailService()
    return AuthService(user_repo, token_service, email_service)


async def get_user_service(db: AsyncSession = Depends(get_db)):
    """Dependency для UserService"""
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    return UserService(user_repo, role_repo)


async def get_admin_service(db: AsyncSession = Depends(get_db)):
    """Dependency для AdminService"""
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    login_history_repo = LoginHistoryRepository(db)
    return AdminService(user_repo, role_repo, login_history_repo)


async def get_token_service(db: AsyncSession = Depends(get_db)):
    """Dependency для TokenService"""
    blacklist_repo = BlacklistRepository(db)
    refresh_repo = RefreshTokenRepository(db)
    user_repo = UserRepository(db)
    return TokenService(blacklist_repo, refresh_repo, user_repo)


# ========== Репозитории ==========

async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_blacklist_repository(db: AsyncSession = Depends(get_db)) -> BlacklistRepository:
    return BlacklistRepository(db)


async def get_refresh_repository(db: AsyncSession = Depends(get_db)) -> RefreshTokenRepository:
    return RefreshTokenRepository(db)


async def get_project_repository(db: AsyncSession = Depends(get_db)) -> ProjectRepository:
    return ProjectRepository(db)
