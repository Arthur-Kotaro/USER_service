# app/api/v1/internal.py
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, user_to_response
from app.schemas.impersonation import (
    ImpersonateRequest, ImpersonateResponse, ImpersonationCloseRequest,
)
from app.config import settings
from app.dependencies import get_current_user
from app.repositories.user_repo import UserRepository
from app.repositories.refresh_repo import RefreshTokenRepository
from app.services.impersonation_service import ImpersonationService

router = APIRouter(tags=["Internal"])


async def verify_internal_key(x_internal_key: str = Header(None)):
    if x_internal_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid internal key")
    return True


@router.get("/users", response_model=List[UserResponse])
async def get_users_internal(
    search: Optional[str] = Query(None, min_length=2),
    limit: int = Query(50, ge=1, le=200),
    _: bool = Depends(verify_internal_key),
    db=Depends(get_db),
):
    stmt = select(User).options(
        selectinload(User.roles), selectinload(User.department), selectinload(User.position)
    ).where(User.deleted_at.is_(None))
    if search:
        p = f"%{search}%"
        stmt = stmt.where(or_(
            User.last_name.ilike(p), User.first_name.ilike(p),
            User.user_name.ilike(p), User.email.ilike(p),
        ))
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    users = result.unique().scalars().all()
    return [user_to_response(u) for u in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_internal(
    user_id: int,
    _: bool = Depends(verify_internal_key),
    db=Depends(get_db),
):
    stmt = select(User).options(
        selectinload(User.roles), selectinload(User.department), selectinload(User.position)
    ).where(User.user_id == user_id, User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.unique().scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_response(user)


@router.post("/auth/impersonate", response_model=ImpersonateResponse)
async def impersonate(
    data: ImpersonateRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = ImpersonationService(
        UserRepository(db),
        RefreshTokenRepository(db),
        settings.USER_SERVICE_URL if hasattr(settings, "USER_SERVICE_URL") else "http://localhost:8000",
    )
    result = await service.impersonate(recipient_id=current_user.user_id, donor_id=data.donor_id)
    return ImpersonateResponse(**result)


@router.post("/auth/impersonation/close")
async def close_impersonation(
    data: ImpersonationCloseRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = ImpersonationService(
        UserRepository(db), RefreshTokenRepository(db), "http://localhost:8000"
    )
    await service.close(data.impersonation_id)
    return {"message": "Impersonation closed"}
