# app/models/__init__.py
from app.models.user import User
from app.models.role import Role, users_roles
from app.models.project import Project, user_projects
from app.models.departament import Department
from app.models.refresh_token import RefreshToken
from app.models.token_blacklist import TokenBlacklist

__all__ = ['User', 'Role', 'users_roles', 'Project', 'user_projects', 'Department', 'RefreshToken', 'TokenBlacklist']
