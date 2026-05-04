from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import (
    LoginRequest, TokenResponse, ChangePasswordRequest,
    PasswordExpiryResponse, PasswordResetRequest
)
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service, get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.login(request)

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.change_password(current_user.user_id, request)

@router.get("/password-expiry", response_model=PasswordExpiryResponse)
async def get_password_expiry(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.get_password_expiry_info(current_user.user_id)

@router.post("/reset-password")
async def reset_password(
    request: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.request_password_reset(request)

@router.post("/refresh")
async def refresh_token(request: dict, auth_service: AuthService = Depends(get_auth_service)):
    refresh_token = request.get("refresh_token")
    if not refresh_token:
        raise HTTPException(400, "refresh_token required")
    return await auth_service.refresh_token(refresh_token)
