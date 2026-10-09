# app/api/v1/__init__.py
from app.api.v1 import auth, users, hr, admin, internal, departments

__all__ = ["auth", "users", "hr", "admin", "internal", "departments"]
