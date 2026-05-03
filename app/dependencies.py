# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.token_service import TokenService
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.repositories.user_repo import UserRepository
from app.repositories.blacklist_repo import BlacklistRepository
from app.repositories.refresh_repo import RefreshTokenRepository
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
    token_service = TokenService(blacklist_repo, refresh_repo)
    
    payload = token_service.decode_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(payload.get("user_id"))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Получить текущего администратора"""
    roles = [r.role_title for r in current_user.roles]
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

async def get_auth_service(db: AsyncSession = Depends(get_db)):
    """Dependency для AuthService"""
    user_repo = UserRepository(db)
    blacklist_repo = BlacklistRepository(db)
    refresh_repo = RefreshTokenRepository(db)
    token_service = TokenService(blacklist_repo, refresh_repo)
    email_service = EmailService()
    
    return AuthService(user_repo, token_service, email_service)
