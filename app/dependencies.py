# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.token_service import TokenService
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.services.user_service import UserService
from app.services.admin_service import AdminService
from app.repositories.user_repo import UserRepository
from app.repositories.refresh_repo import RefreshTokenRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.department_repo import DepartmentRepository
from app.repositories.position_repo import PositionRepository
from app.repositories.login_history_repo import LoginHistoryRepository
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    refresh_repo = RefreshTokenRepository(db)
    user_repo = UserRepository(db)
    token_service = TokenService(refresh_repo, user_repo)

    payload = await token_service.decode_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_repo.get_by_id(payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deleted")

    if user.blocked_at is not None:
        from datetime import datetime, timezone
        if user.block_expires_at is None or user.block_expires_at > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is blocked: {user.blocked_reason or 'No reason'}",
            )

    if user.locked_until is not None:
        from datetime import datetime, timezone
        if user.locked_until > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account temporarily locked until {user.locked_until.isoformat()}",
            )

    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.is_super_admin:
        return current_user
    if "admin" not in current_user.get_role_codes():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


async def get_current_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin privileges required")
    return current_user


async def get_auth_service(db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    refresh_repo = RefreshTokenRepository(db)
    login_history_repo = LoginHistoryRepository(db)
    token_service = TokenService(refresh_repo, user_repo)
    email_service = EmailService()
    return AuthService(user_repo, token_service, email_service, login_history_repo)


async def get_user_service(db: AsyncSession = Depends(get_db)):
    return UserService(
        UserRepository(db),
        RoleRepository(db),
        DepartmentRepository(db),
        PositionRepository(db),
    )


async def get_admin_service(db: AsyncSession = Depends(get_db)):
    return AdminService(
        UserRepository(db),
        RoleRepository(db),
        LoginHistoryRepository(db),
    )


async def get_token_service(db: AsyncSession = Depends(get_db)):
    return TokenService(RefreshTokenRepository(db), UserRepository(db))
