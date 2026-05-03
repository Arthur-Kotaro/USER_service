# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import (
    LoginRequest, TokenResponse, ChangePasswordRequest, 
    PasswordExpiryResponse, PasswordResetRequest
)
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service, get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    """
    Проверяет email/пароль, возвращает access и refresh токены.
    """
    return await auth_service.login(request)

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Смена пароля пользователем"""
    return await auth_service.change_password(current_user.user_id, request)

@router.get("/password-expiry", response_model=PasswordExpiryResponse)
async def get_password_expiry(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Получение оставшегося времени действия пароля"""
    return await auth_service.get_password_expiry_info(current_user.user_id)

@router.post("/reset-password")
async def reset_password(
    request: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Запрос на восстановление доступа (отправка временного пароля на почту)"""
    return await auth_service.request_password_reset(request)
