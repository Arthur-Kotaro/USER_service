# app/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from app.repositories.user_repo import UserRepository
from app.services.token_service import TokenService
from app.utils.hasher import verify_password, hash_password
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

class AuthService:
    def __init__(self, user_repo: UserRepository, token_service: TokenService):
        self.user_repo = user_repo
        self.token_service = token_service
    
    async def login(self, login_data: LoginRequest) -> TokenResponse:
        """Аутентификация пользователя"""
        # Находим пользователя по email
        user = await self.user_repo.get_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Проверяем пароль
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Проверяем активен ли пользователь
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        # Создаем токены
        access_token = self.token_service.create_access_token(
            data={"user_id": user.id, "email": user.email}
        )
        refresh_token = self.token_service.create_refresh_token(
            data={"user_id": user.id}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    async def register(self, register_data: RegisterRequest) -> dict:
        """Регистрация нового пользователя"""
        # Проверяем, не существует ли пользователь
        existing_user = await self.user_repo.get_by_email(register_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Проверяем совпадение паролей
        if register_data.password != register_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        # Создаем нового пользователя
        hashed_password = hash_password(register_data.password)
        user = await self.user_repo.create(
            email=register_data.email,
            username=register_data.username,
            hashed_password=hashed_password
        )
        
        return {"message": "User registered successfully", "user_id": user.id}
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Обновление access token"""
        # Проверяем refresh token
        token_data = self.token_service.verify_refresh_token(refresh_token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Получаем пользователя
        user = await self.user_repo.get_by_id(token_data.get("user_id"))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Создаем новые токены
        access_token = self.token_service.create_access_token(
            data={"user_id": user.id, "email": user.email}
        )
        new_refresh_token = self.token_service.create_refresh_token(
            data={"user_id": user.id}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
