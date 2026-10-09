# app/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.user import UserResponse, UserUpdate, user_to_response
from app.schemas.auth import ChangePasswordRequest
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.token_service import TokenService
from app.repositories.user_repo import UserRepository
from app.repositories.role_repo import RoleRepository
from app.repositories.department_repo import DepartmentRepository
from app.repositories.position_repo import PositionRepository
from app.repositories.refresh_repo import RefreshTokenRepository
from app.repositories.login_history_repo import LoginHistoryRepository
from app.models.user import User

router = APIRouter(tags=["Users"])


def _make_user_service(db) -> UserService:
    return UserService(
        UserRepository(db),
        RoleRepository(db),
        DepartmentRepository(db),
        PositionRepository(db),
    )


def _make_auth_service(db) -> AuthService:
    user_repo = UserRepository(db)
    refresh_repo = RefreshTokenRepository(db)
    login_history_repo = LoginHistoryRepository(db)
    token_service = TokenService(refresh_repo, user_repo)
    return AuthService(user_repo, token_service, None, login_history_repo)


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return user_to_response(current_user)


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = _make_user_service(db)
    update_dict = update_data.model_dump(exclude_unset=True)
    user = await service.update_user(current_user.user_id, update_dict)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.post("/me/change-password")
async def change_my_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    auth_service = _make_auth_service(db)
    return await auth_service.change_password(current_user.user_id, request)


@router.get("/me/status")
async def get_my_status(current_user: User = Depends(get_current_user)):
    from app.schemas.user import get_user_status_from_model
    return {
        "user_id": current_user.user_id,
        "user_name": current_user.user_name,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "status": get_user_status_from_model(current_user),
        "is_blocked": current_user.blocked_at is not None,
        "is_deleted": current_user.deleted_at is not None,
        "is_super_admin": current_user.is_super_admin,
        "position_code": current_user.position.position_code if current_user.position else None,
        "dept_code": current_user.department.dept_code if current_user.department else None,
        "roles": current_user.get_role_codes(),
    }


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = _make_user_service(db)
    users = await service.get_all_users(skip, limit, only_active=True)
    if search:
        s = search.lower()
        users = [
            u for u in users
            if s in u.user_name.lower()
            or s in (u.last_name or "").lower()
            or s in (u.first_name or "").lower()
            or (u.email and s in u.email.lower())
        ]
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = _make_user_service(db)
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.post("/me/logout-all")
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    token_service = TokenService(RefreshTokenRepository(db), UserRepository(db))
    revoked = await token_service.revoke_all_user_refresh_tokens(current_user.user_id)
    return {"message": "Logged out from all devices", "revoked_tokens": revoked}
