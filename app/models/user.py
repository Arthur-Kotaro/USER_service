# app/models/user.py
from sqlalchemy import (
    Column, BigInteger, SmallInteger, String, Boolean, DateTime, Date,
    ForeignKey, CheckConstraint, Index, text, Integer, JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import List
from datetime import datetime, timezone, timedelta
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_name = Column(String(100), unique=True, nullable=False, index=True)
    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    gender = Column(String(1), nullable=True)
    birth_date = Column(Date, nullable=True)

    phone_work = Column(String(20), nullable=True)
    phone_mobile = Column(String(20), nullable=True)

    position_id = Column(SmallInteger, ForeignKey("positions.position_id"), nullable=False)
    dept_id = Column(UUID(as_uuid=True), ForeignKey("departments.dept_id", ondelete="SET NULL"), nullable=True)

    blocked_at = Column(DateTime(timezone=True), nullable=True)
    blocked_reason = Column(String, nullable=True)
    blocked_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    block_expires_at = Column(DateTime(timezone=True), nullable=True)

    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    deleted_at = Column(DateTime(timezone=True), nullable=True)

    password_updated_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
    password_history = Column(JSON, default=[])
    temp_password = Column(String(255), nullable=True)
    temp_password_expires_at = Column(DateTime(timezone=True), nullable=True)

    is_super_admin = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(BigInteger, nullable=True)

    position = relationship("Position", lazy="joined")
    department = relationship("Department", back_populates="users", lazy="joined")
    roles = relationship("Role", secondary="users_roles", back_populates="users", lazy="selectin")
    blocked_by_user = relationship("User", remote_side=[user_id], foreign_keys=[blocked_by])
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("gender IN ('M', 'F')", name="user_gender_check"),
        Index("idx_users_dept", "dept_id"),
        Index("idx_users_position", "position_id"),
        Index("idx_users_email", "email"),
        Index("idx_users_deleted_at", "deleted_at", postgresql_where=(text("deleted_at IS NULL"))),
        Index("idx_users_blocked_at", "blocked_at", postgresql_where=(text("blocked_at IS NOT NULL"))),
        Index("idx_users_last_login", "last_login_at"),
    )

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    @property
    def is_active(self) -> bool:
        return self.blocked_at is None and self.deleted_at is None

    @property
    def is_blocked(self) -> bool:
        return self.blocked_at is not None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_blocked_permanently(self) -> bool:
        return self.is_blocked and self.block_expires_at is None

    @property
    def is_blocked_temporarily(self) -> bool:
        if not self.is_blocked or self.block_expires_at is None:
            return False
        return self.block_expires_at > datetime.now(timezone.utc)

    @property
    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return self.locked_until > datetime.now(timezone.utc)

    def can_login(self) -> tuple:
        if self.deleted_at is not None:
            return False, "Account is deleted"
        if self.blocked_at is not None:
            if self.block_expires_at is not None and self.block_expires_at <= datetime.now(timezone.utc):
                return True, None
            return False, self.blocked_reason or "Account is blocked"
        if self.locked_until is not None and self.locked_until > datetime.now(timezone.utc):
            return False, f"Account locked until {self.locked_until.isoformat()}"
        return True, None

    def record_failed_login(self) -> None:
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)

    def reset_failed_attempts(self) -> None:
        self.failed_login_attempts = 0
        self.locked_until = None

    def change_password(self, new_password_hash: str) -> None:
        if self.password_hash:
            history = self.password_history or []
            if len(history) >= 3:
                history = history[1:]
            history.append(self.password_hash)
            self.password_history = history
        self.password_hash = new_password_hash
        self.password_updated_at = datetime.now(timezone.utc)

    def is_password_expired(self) -> bool:
        if not self.password_updated_at:
            return True
        return (datetime.now(timezone.utc) - self.password_updated_at).days > 60

    def check_password_history(self, new_password_hash: str) -> bool:
        if not self.password_history:
            return True
        return new_password_hash not in self.password_history

    def has_role(self, role_code: str) -> bool:
        if not self.roles:
            return False
        return any(r.role_code == role_code for r in self.roles)

    def get_role_codes(self) -> List[str]:
        return [r.role_code for r in self.roles] if self.roles else []

    def get_role_titles(self) -> List[str]:
        return [r.role_name_ru for r in self.roles] if self.roles else []

    def block(self, reason: str, blocked_by_user_id: int, expires_at=None) -> None:
        self.blocked_at = datetime.now(timezone.utc)
        self.blocked_reason = reason
        self.blocked_by = blocked_by_user_id
        self.block_expires_at = expires_at

    def unblock(self) -> None:
        self.blocked_at = None
        self.blocked_reason = None
        self.blocked_by = None
        self.block_expires_at = None

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        self.deleted_at = None

    def __repr__(self):
        return f"<User(user_id={self.user_id}, user_name='{self.user_name}')>"
