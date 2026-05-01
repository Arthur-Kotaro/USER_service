# app/dependencies.py
from fastapi import HTTPException, status
from app.models.user import User

async def prevent_self_registration():
    """Обычные пользователи не могут регистрироваться"""
    # Эта зависимость должна использоваться только для admin endpoints
    pass

async def prevent_self_deletion(current_user: User):
    """Пользователи не могут удалять свои профили"""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Users cannot delete their own profiles. Contact administrator."
    )

async def require_admin_for_user_management(current_user: User):
    """Требовать права админа для управления пользователями"""
    has_admin_role = any(role.role_title == "admin" for role in current_user.roles)
    if not has_admin_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User management requires admin privileges"
        )
    return current_user
