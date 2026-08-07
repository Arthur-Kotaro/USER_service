# app/services/auth_service.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.repositories.user_repo import UserRepository
from app.services.token_service import TokenService
from app.services.email_service import EmailService
from app.utils.hasher import verify_password, hash_password, generate_random_token
from app.schemas.auth import (
    LoginRequest, TokenResponse, ChangePasswordRequest,
    PasswordExpiryResponse, PasswordResetRequest
)
from app.models.user import User
from app.models.login_history import LoginHistory


class AuthService:
    def __init__(self, user_repo: UserRepository, token_service: TokenService, email_service: EmailService):
        self.user_repo = user_repo
        self.token_service = token_service
        self.email_service = email_service
        self.password_expiry_days = 60

    async def _log_login_attempt(
        self, 
        user_id: Optional[int], 
        status: str, 
        failure_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> None:
        """Логирование попытки входа"""
        try:
            login_history = LoginHistory(
                user_id=user_id,
                login_status=status,
                failure_reason=failure_reason,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id
            )
            self.user_repo.db.add(login_history)
            await self.user_repo.db.commit()
        except Exception as e:
            print(f"Failed to log login attempt: {e}")

    async def _check_user_can_login(self, user: User) -> Tuple[bool, Optional[str]]:
        """
        Проверка возможности входа пользователя.
        Возвращает (разрешено, причина_отказа)
        """
        # Проверка на soft delete
        if user.deleted_at is not None:
            return False, "Account is deleted"
        
        # Проверка на блокировку
        if user.blocked_at is not None:
            # Если временная блокировка истекла - автоматически разблокируем
            if user.block_expires_at is not None:
                if user.block_expires_at <= datetime.now(timezone.utc):
                    # Автоматическая разблокировка
                    await self.user_repo.unblock_user(user.user_id)
                    return True, None
            return False, user.blocked_reason or "Account is blocked"
        
        return True, None

    async def login(
        self, 
        login_data: LoginRequest, 
        request: Optional[Request] = None
    ) -> TokenResponse:
        # Получаем информацию о запросе для логирования
        client_ip = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        # 1. Получаем пользователя по email
        user = await self.user_repo.get_by_email(login_data.email)
        if not user:
            await self._log_login_attempt(
                user_id=None,
                status="failed",
                failure_reason="User not found",
                ip_address=client_ip,
                user_agent=user_agent
            )
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Сохраняем ID пользователя для дальнейшего использования
        user_id = user.user_id

        # 2. Проверка пароля
        is_valid = verify_password(login_data.password, user.password_hash)
        is_temp_valid = False
        using_temp_password = False
        
        if not is_valid and user.temp_password:
            is_temp_valid = verify_password(login_data.password, user.temp_password)
            if is_temp_valid and user.temp_password_expires_at:
                if user.temp_password_expires_at <= datetime.now(timezone.utc):
                    is_temp_valid = False
                else:
                    using_temp_password = True

        if not is_valid and not is_temp_valid:
            await self._log_login_attempt(
                user_id=user_id,
                status="failed",
                failure_reason="Invalid password",
                ip_address=client_ip,
                user_agent=user_agent
            )
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # 3. Проверка возможности входа (блокировка/удаление)
        can_login, block_reason = await self._check_user_can_login(user)
        if not can_login:
            await self._log_login_attempt(
                user_id=user_id,
                status="blocked",
                failure_reason=block_reason,
                ip_address=client_ip,
                user_agent=user_agent
            )
            raise HTTPException(status_code=403, detail=block_reason or "Account is blocked")

        # 4. Если использован временный пароль - очищаем
        if using_temp_password:
            await self.user_repo.clear_temp_password(user_id)

        # 5. Обновляем last_login_at
        await self.user_repo.update_last_login(user_id)

        # 6. Загружаем связи пользователя асинхронно через awaitable_attrs
        projects = await user.awaitable_attrs.projects
        roles = await user.awaitable_attrs.roles

        # Преобразуем в список названий
        project_titles = [p.project_title for p in projects] if projects else []
        role_titles = [r.role_title for r in roles] if roles else []
        role = role_titles[0] if role_titles else "user"

        # 7. Создаём токены
        access_token = self.token_service.create_access_token(
            user_id=user_id,
            projects=project_titles,
            role=role
        )
        refresh_token = await self.token_service.create_refresh_token(user_id)

        # 8. Логируем успешный вход
        await self._log_login_attempt(
            user_id=user_id,
            status="success",
            ip_address=client_ip,
            user_agent=user_agent
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    async def change_password(self, user_id: int, request: ChangePasswordRequest) -> dict:
        if request.new_password != request.confirm_password:
            raise HTTPException(400, "New passwords do not match")
        if len(request.new_password) < 6:
            raise HTTPException(400, "Password must be at least 6 characters")
        
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(404, "User not found")
        
        # Проверка на удалённого пользователя
        if user.deleted_at is not None:
            raise HTTPException(403, "Account is deleted")
        
        if not verify_password(request.current_password, user.password_hash):
            raise HTTPException(401, "Current password is incorrect")
        
        new_hashed = hash_password(request.new_password)
        await self.user_repo.update_password(user.user_id, new_hashed)
        await self.user_repo.clear_temp_password(user.user_id)
        
        # Отзываем все refresh токены
        await self.token_service.revoke_all_user_refresh_tokens(user.user_id)
        
        return {"message": "Password changed successfully. Please login again."}

    async def get_password_expiry_info(self, user_id: int) -> PasswordExpiryResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(404, "User not found")
        
        # Проверка на удалённого пользователя
        if user.deleted_at is not None:
            raise HTTPException(403, "Account is deleted")
        
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
        user = await self.user_repo.get_by_email(request.email)
        
        # Не раскрываем информацию о существовании пользователя
        if not user or not user.email:
            return {"message": "If an account with this email exists, a temporary password has been sent"}
        
        # Проверка на удалённого пользователя
        if user.deleted_at is not None:
            return {"message": "If an account with this email exists, a temporary password has been sent"}
        
        temp_password = generate_random_token(10)
        temp_password_hash = hash_password(temp_password)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        await self.user_repo.set_temp_password(user.user_id, temp_password_hash, expires_at)
        
        sent = await self.email_service.send_temp_password(user.email, temp_password, user.user_name)
        if not sent:
            raise HTTPException(500, "Failed to send email. Please contact administrator.")
        
        return {"message": "Temporary password has been sent to your email"}

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        new_access_token = await self.token_service.refresh_access_token(refresh_token)
        if not new_access_token:
            raise HTTPException(401, "Invalid or expired refresh token")
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        """Отзыв конкретного refresh токена"""
        await self.token_service.revoke_refresh_token(refresh_token)

    async def revoke_all_user_refresh_tokens(self, user_id: int) -> None:
        """Отзыв всех refresh токенов пользователя"""
        await self.token_service.revoke_all_user_refresh_tokens(user_id)
