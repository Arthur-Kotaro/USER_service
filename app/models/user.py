# app/models/user.py (ОБНОВЛЁННАЯ ВЕРСИЯ)
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Date, ForeignKey, CheckConstraint, Index, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional
from app.database import Base

class User(Base):
    __tablename__ = "users"

    # Основные поля
    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_name = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    gender = Column(String(1), CheckConstraint("gender IN ('M', 'F')"), nullable=True)
    birth_date = Column(Date, nullable=True)

    # Контактные телефоны
    phone_work = Column(String(20), nullable=True)
    phone_mobile = Column(String(20), nullable=True)

    # Внешние ключи
    dept_code = Column(String(20), ForeignKey("department.dept_code", ondelete="SET NULL"), nullable=True)

    # Блокировка (status удалён, блокировка определяется по blocked_at)
    blocked_at = Column(DateTime(timezone=True), nullable=True)
    blocked_reason = Column(String, nullable=True)
    blocked_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    block_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Поля для управления паролем
    password_updated_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
    temp_password = Column(String(255), nullable=True)
    temp_password_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Аудит
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Связи
    roles = relationship("Role", secondary="users_roles", back_populates="users", lazy="selectin")
    projects = relationship("Project", secondary="user_projects", back_populates="users", lazy="selectin")
    department = relationship("Department", back_populates="users")
    blocked_by_user = relationship("User", remote_side=[user_id], foreign_keys=[blocked_by])
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    # Индексы и ограничения
    __table_args__ = (
        CheckConstraint("gender IN ('M', 'F')", name="user_gender_check"),
        Index("idx_users_gender", "gender"),
        Index("idx_users_birth_date", "birth_date"),
        Index("idx_users_dept_code", "dept_code"),
        Index("idx_users_deleted_at", "deleted_at", postgresql_where=(text("deleted_at IS NULL"))),
        Index("idx_users_blocked_at", "blocked_at", postgresql_where=(text("blocked_at IS NOT NULL"))),
        Index("idx_users_last_login", "last_login_at"),
        Index("idx_users_dept_blocked", "dept_code", "blocked_at"),
        Index("idx_users_phone_work", "phone_work", postgresql_where=(text("phone_work IS NOT NULL"))),
        Index("idx_users_phone_mobile", "phone_mobile", postgresql_where=(text("phone_mobile IS NOT NULL"))),
    )

    # ========== Свойства (properties) ==========
    
    @property
    def is_active(self) -> bool:
        """Пользователь активен = не заблокирован и не удалён"""
        return self.blocked_at is None and self.deleted_at is None

    @property
    def is_blocked(self) -> bool:
        """Пользователь заблокирован"""
        return self.blocked_at is not None

    @property
    def is_deleted(self) -> bool:
        """Пользователь удалён (soft delete)"""
        return self.deleted_at is not None
    
    @property
    def is_blocked_permanently(self) -> bool:
        """Бессрочная блокировка"""
        return self.is_blocked and self.block_expires_at is None
    
    @property
    def is_blocked_temporarily(self) -> bool:
        """Временная блокировка"""
        if not self.is_blocked or self.block_expires_at is None:
            return False
        from datetime import datetime, timezone
        return self.block_expires_at > datetime.now(timezone.utc)
    
    @property
    def block_is_expired(self) -> bool:
        """Проверка, истекла ли временная блокировка"""
        if not self.is_blocked or self.block_expires_at is None:
            return False
        from datetime import datetime, timezone
        return self.block_expires_at <= datetime.now(timezone.utc)

    # ========== Методы ==========

    def can_login(self) -> tuple[bool, Optional[str]]:
        """
        Проверка возможности входа.
        Возвращает (разрешено, причина_отказа)
        """
        # Проверка на удаление
        if self.deleted_at is not None:
            return False, "Account is deleted"
        
        # Проверка на блокировку
        if self.blocked_at is not None:
            # Если временная блокировка истекла - можно войти
            if self.block_expires_at is not None:
                from datetime import datetime, timezone
                if self.block_expires_at <= datetime.now(timezone.utc):
                    return True, None
            return False, "Account is blocked"
        
        return True, None

    def block(self, reason: str, blocked_by_user_id: int, expires_at: Optional[datetime] = None) -> None:
        """
        Блокировка пользователя
        """
        from datetime import datetime, timezone
        self.blocked_at = datetime.now(timezone.utc)
        self.blocked_reason = reason
        self.blocked_by = blocked_by_user_id
        self.block_expires_at = expires_at

    def unblock(self) -> None:
        """Разблокировка пользователя"""
        self.blocked_at = None
        self.blocked_reason = None
        self.blocked_by = None
        self.block_expires_at = None

    def soft_delete(self, deleted_by_user_id: Optional[int] = None) -> None:
        """Мягкое удаление пользователя"""
        from datetime import datetime, timezone
        self.deleted_at = datetime.now(timezone.utc)
        # Опционально: сохранить кто удалил (потребуется добавить поле deleted_by)
        # self.deleted_by = deleted_by_user_id

    def restore(self) -> None:
        """Восстановление пользователя после soft delete"""
        self.deleted_at = None

    @property
    def has_temp_password(self) -> bool:
        """Проверка наличия активного временного пароля"""
        from datetime import datetime, timezone
        if not self.temp_password or not self.temp_password_expires_at:
            return False
        return self.temp_password_expires_at > datetime.now(timezone.utc)

    def __repr__(self):
        return f"<User(user_id={self.user_id}, user_name='{self.user_name}', email='{self.email}')>"
