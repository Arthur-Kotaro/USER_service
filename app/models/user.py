from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Date, ForeignKey, CheckConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional, List
from app.database import Base

class User(Base):
    __tablename__ = "users"

    # Основные поля
    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_name = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    gender = Column(String(1))
    birth_date = Column(Date, nullable=True)

    # Контактные телефоны
    phone_work = Column(String(20), nullable=True)
    phone_mobile = Column(String(20), nullable=True)

    # Внешние ключи
    dept_code = Column(String(20), ForeignKey("departament.dept_code", ondelete="SET NULL"))

    # Статус и блокировка
    status = Column(String(20), nullable=False, server_default="active")
    blocked_at = Column(DateTime(timezone=True), nullable=True)
    blocked_reason = Column(String, nullable=True)
    blocked_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    block_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Поля для управления паролем
    password_updated_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
    temp_password = Column(String(255), nullable=True)
    temp_password_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Аудит
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Связи (все с одинаковым отступом)
    roles = relationship("Role", secondary="users_roles", back_populates="users", lazy="selectin")
    projects = relationship("Project", secondary="user_projects", back_populates="users", lazy="selectin")
    department = relationship("Department", back_populates="users")
    blocked_by_user = relationship("User", remote_side=[user_id], foreign_keys=[blocked_by])
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    # Индексы и ограничения
    __table_args__ = (
        CheckConstraint("gender IN ('M', 'F')", name="user_gender_check"),
        CheckConstraint("status IN ('active', 'blocked', 'archived')", name="user_status_check"),
        Index("idx_users_gender", "gender"),
        Index("idx_users_birth_date", "birth_date"),
        Index("idx_users_dept_code", "dept_code"),
        Index("idx_users_status", "status"),
        Index("idx_users_status_username", "status", "user_name"),
        Index("idx_users_blocked_at", "blocked_at", postgresql_where=(status == "blocked")),
        Index("idx_users_last_login", "last_login_at"),
        Index("idx_users_dept_status", "dept_code", "status"),
        Index("idx_users_phone_work", "phone_work"),
        Index("idx_users_phone_mobile", "phone_mobile"),
    )

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_blocked(self) -> bool:
        return self.status == "blocked"

    def can_login(self) -> bool:
        return self.status == "active"

    @property
    def has_temp_password(self) -> bool:
        from datetime import datetime, timezone
        if not self.temp_password or not self.temp_password_expires_at:
            return False
        return self.temp_password_expires_at > datetime.now(timezone.utc)
