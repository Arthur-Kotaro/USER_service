from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    """
    Проверяет логин/пароль, возвращает access и refresh токены.
    """
    tokens = await auth_service.authenticate(request.username, request.password)
    if not tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return tokens




class AuthService:
    def __init__(self, user_repo, token_service):
        self.user_repo = user_repo
        self.token_service = token_service

    async def authenticate(self, username: str, password: str):
        user = await self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.password_hash) or not user.is_active:
            # Логирование неудачной попытки
            logger.warning(f"Failed login attempt for {username}")
            return None
        projects = json.loads(user.projects)
        access_token = self.token_service.create_access_token(user.id, projects, user.role)
        refresh_token = self.token_service.create_refresh_token(user.id)
        # Логирование успеха
        logger.info(f"User {username} logged in")
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
