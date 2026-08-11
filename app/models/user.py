# app/models/user.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Date, ForeignKey, CheckConstraint, Index, text, Integer, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from app.database import Base


class User(Base):
    __tablename__ = "users"

    # Основные поля
    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_name = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=True)  # НОВОЕ ПОЛЕ
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    gender = Column(String(1), CheckConstraint("gender IN ('M', 'F')"), nullable=True)
    birth_date = Column(Date, nullable=True)

    # Контактные телефоны
    phone_work = Column(String(20), nullable=True)
    phone_mobile = Column(String(20), nullable=True)

    # Внешние ключи
    dept_code = Column(String(20), ForeignKey("department.dept_code", ondelete="SET NULL"), nullable=True)

    # НОВОЕ ПОЛЕ: Иерархия (начальник-подчиненный)
    head_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)

    # Блокировка
    blocked_at = Column(DateTime(timezone=True), nullable=True)
    blocked_reason = Column(String, nullable=True)
    blocked_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    block_expires_at = Column(DateTime(timezone=True), nullable=True)

    # НОВЫЕ ПОЛЯ: Безопасность
    failed_login_attempts = Column(Integer, default=0)  # Счетчик неудачных попыток
    locked_until = Column(DateTime(timezone=True), nullable=True)  # Временная блокировка

    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Поля для управления паролем
    password_updated_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
    password_history = Column(JSON, default=[])  # НОВОЕ ПОЛЕ: хеши последних 3 паролей
    temp_password = Column(String(255), nullable=True)
    temp_password_expires_at = Column(DateTime(timezone=True), nullable=True)

    # НОВОЕ ПОЛЕ: Супер-админ
    is_super_admin = Column(Boolean, default=False)

    # Аудит
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(BigInteger, nullable=True)  # Кто создал (HR или супер-админ)

    # Связи
    roles = relationship("Role", secondary="users_roles", back_populates="users", lazy="selectin")
    projects = relationship("Project", secondary="user_projects", back_populates="users", lazy="selectin")
    department = relationship("Department", back_populates="users")
    blocked_by_user = relationship("User", remote_side=[user_id], foreign_keys=[blocked_by])
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    head = relationship("User", remote_side=[user_id], foreign_keys=[head_id], backref="subordinates")

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
        Index("idx_users_head_id", "head_id"),
#        Index("idx_users_super_admin", "is_super_admin", postgresql_where=(text("is_super_admin = TRUE"))),
    )

    # ========== Свойства ==========

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
        return self.block_expires_at > datetime.now(timezone.utc)

    @property
    def block_is_expired(self) -> bool:
        """Проверка, истекла ли временная блокировка"""
        if not self.is_blocked or self.block_expires_at is None:
            return False
        return self.block_expires_at <= datetime.now(timezone.utc)

#    @property
#    def is_super_admin(self) -> bool:
#        """Является ли пользователь супер-админом"""
#        return self.is_super_admin

    @property
    def is_locked(self) -> bool:
        """Временная блокировка после неудачных попыток"""
        if self.locked_until is None:
            return False
        return self.locked_until > datetime.now(timezone.utc)

    @property
    def lock_is_expired(self) -> bool:
        """Истекла ли временная блокировка"""
        if self.locked_until is None:
            return False
        return self.locked_until <= datetime.now(timezone.utc)

    # ========== Методы ==========

    # app/models/user.py - исправленный метод can_login

    def can_login(self) -> tuple[bool, Optional[str]]:
        """
        Проверка возможности входа.
        Возвращает (разрешено, причина_отказа)
        Использует только уже загруженные атрибуты
        """
        # Проверка на удаление (используем getattr, чтобы избежать ленивой загрузки)
        deleted_at = getattr(self, 'deleted_at', None)
        if deleted_at is not None:
            return False, "Account is deleted"

        # Проверка на блокировку
        blocked_at = getattr(self, 'blocked_at', None)
        if blocked_at is not None:
            block_expires_at = getattr(self, 'block_expires_at', None)
            if block_expires_at is not None:
                if block_expires_at <= datetime.now(timezone.utc):
                    return True, None
            return False, getattr(self, 'blocked_reason', "Account is blocked")

        # Проверка на временную блокировку (после неудачных попыток)
        locked_until = getattr(self, 'locked_until', None)
        if locked_until is not None:
            if locked_until > datetime.now(timezone.utc):
                return False, f"Account locked until {locked_until.isoformat()}"
            # Если истекло - снимаем блокировку
            self.locked_until = None
            self.failed_login_attempts = 0

        return True, None

    def record_failed_login(self) -> None:
        """Увеличить счетчик неудачных попыток"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)

    def reset_failed_attempts(self) -> None:
        """Сбросить счетчик после успешного входа"""
        self.failed_login_attempts = 0
        self.locked_until = None

    def change_password(self, new_password_hash: str) -> None:
        """Сменить пароль с сохранением истории"""
        # Сохраняем текущий хеш в историю (если есть)
        if self.password_hash:
            history = self.password_history or []
            if len(history) >= 3:
                history = history[1:]  # Удаляем самый старый
            history.append(self.password_hash)
            self.password_history = history

        # Устанавливаем новый пароль
        self.password_hash = new_password_hash
        self.password_updated_at = datetime.now(timezone.utc)

    def is_password_expired(self) -> bool:
        """Проверить, не истек ли срок пароля (60 дней)"""
        if not self.password_updated_at:
            return True
        days_since_update = (datetime.now(timezone.utc) - self.password_updated_at).days
        return days_since_update > 60

    def check_password_history(self, new_password_hash: str) -> bool:
        """Проверить, не использовался ли пароль ранее (последние 3)"""
        if not self.password_history:
            return True
        return new_password_hash not in self.password_history

    def has_role(self, role: str) -> bool:
        """Проверить наличие роли по названию"""
        if not self.roles:
            return False
        return any(r.role_title == role for r in self.roles)

    def has_role_code(self, role_code: str) -> bool:
        """Проверить наличие роли по коду"""
        if not self.roles:
            return False
        return any(r.role_code == role_code for r in self.roles)

    def block(self, reason: str, blocked_by_user_id: int, expires_at: Optional[datetime] = None) -> None:
        """Блокировка пользователя"""
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
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Восстановление пользователя после soft delete"""
        self.deleted_at = None

    @property
    def has_temp_password(self) -> bool:
        """Проверка наличия активного временного пароля"""
        if not self.temp_password or not self.temp_password_expires_at:
            return False
        return self.temp_password_expires_at > datetime.now(timezone.utc)

    def get_roles_titles(self) -> List[str]:
        """Получить список названий ролей"""
        return [r.role_title for r in self.roles] if self.roles else []

    def get_projects_titles(self) -> List[str]:
        """Получить список названий проектов"""
        return [p.project_title for p in self.projects] if self.projects else []

    def __repr__(self):
        return f"<User(user_id={self.user_id}, user_name='{self.user_name}', email='{self.email}')>"
