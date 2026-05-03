# app/services/auth_service.py - полный файл
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.user_repo import UserRepository
from app.services.token_service import TokenService
from app.services.email_service import EmailService
from app.utils.hasher import verify_password, hash_password, generate_random_token
from app.schemas.auth import (
    LoginRequest, TokenResponse, ChangePasswordRequest, 
    PasswordExpiryResponse, PasswordResetRequest
)
from app.models.user import User

class AuthService:
    def __init__(self, user_repo: UserRepository, token_service: TokenService, email_service: EmailService):
        self.user_repo = user_repo
        self.token_service = token_service
        self.email_service = email_service
        self.password_expiry_days = 60  # 2 месяца
    
    async def login(self, login_data: LoginRequest) -> TokenResponse:
        """Аутентификация пользователя"""
        user = await self.user_repo.get_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Проверяем пароль (сначала обычный, потом временный)
        is_valid = verify_password(login_data.password, user.password_hash)
        is_temp_valid = False
        
        if not is_valid and user.temp_password:
            is_temp_valid = verify_password(login_data.password, user.temp_password)
            if is_temp_valid:
                # Проверяем срок действия временного пароля
                if user.temp_password_expires_at and user.temp_password_expires_at > datetime.now(timezone.utc):
                    pass  # Временный пароль действителен
                else:
                    is_temp_valid = False
        
        if not is_valid and not is_temp_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        # Обновляем время последнего входа
        await self.user_repo.update_last_login(user.user_id)
        
        # Создаем токены
        projects = [p.project_title for p in user.projects] if user.projects else []
        roles = [r.role_title for r in user.roles] if user.roles else []
        role = roles[0] if roles else "user"
        
        access_token = self.token_service.create_access_token(
            user_id=user.user_id,
            projects=projects,
            role=role
        )
        refresh_token = self.token_service.create_refresh_token(user.user_id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    async def change_password(self, user_id: int, request: ChangePasswordRequest) -> dict:
        """Смена пароля пользователем"""
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New passwords do not match"
            )
        
        if len(request.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters"
            )
        
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Проверяем текущий пароль
        if not verify_password(request.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Обновляем пароль
        new_hashed = hash_password(request.new_password)
        await self.user_repo.update_password(user.user_id, new_hashed)
        
        # Очищаем временный пароль если был
        await self.user_repo.clear_temp_password(user.user_id)
        
        # Инвалидируем все refresh токены пользователя
        await self.token_service.revoke_all_user_refresh_tokens(user.user_id)
        
        return {"message": "Password changed successfully. Please login again."}
    
    async def get_password_expiry_info(self, user_id: int) -> PasswordExpiryResponse:
        """Получение информации о сроке действия пароля"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        last_updated = user.password_updated_at or user.created_at
        if last_updated:
            expires_at = last_updated + timedelta(days=self.password_expiry_days)
            now = datetime.now(timezone.utc)
            days_remaining = (expires_at - now).days
            is_expired = days_remaining <= 0
        else:
            expires_at = None
            days_remaining = self.password_expiry_days
            is_expired = False
        
        return PasswordExpiryResponse(
            days_remaining=max(0, days_remaining),
            is_expired=is_expired,
            expires_at=expires_at
        )
    
    async def request_password_reset(self, request: PasswordResetRequest) -> dict:
        """Запрос на восстановление доступа (генерация временного пароля)"""
        user = await self.user_repo.get_by_email(request.email)
        if not user:
            # Не раскрываем информацию о существовании пользователя
            return {"message": "If an account with this email exists, a temporary password has been sent"}
        
        if not user.email:
            return {"message": "If an account with this email exists, a temporary password has been sent"}
        
        # Генерируем временный пароль
        temp_password = generate_random_token(10)  # 10 символов
        temp_password_hash = hash_password(temp_password)
        
        # Сохраняем временный пароль (действителен 24 часа)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        await self.user_repo.set_temp_password(user.user_id, temp_password_hash, expires_at)
        
        # Отправляем на почту
        sent = await self.email_service.send_temp_password(user.email, temp_password, user.user_name)
        
        if not sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email. Please contact administrator."
            )
        
        return {"message": "Temporary password has been sent to your email"}
