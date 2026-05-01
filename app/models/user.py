# app/models/user.py
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
    gender = Column(String(1), CheckConstraint("gender IN ('M', 'F')"))
    birth_date = Column(Date, nullable=True)
    
    # Внешние ключи
    dept_code = Column(String(20), ForeignKey("departament.dept_code", ondelete="SET NULL"))
    
    # Статус и блокировка
    status = Column(String(20), nullable=False, default="active", 
                   CheckConstraint("status IN ('active', 'blocked', 'archived')"))
    blocked_at = Column(DateTime(timezone=True), nullable=True)
    blocked_reason = Column(String, nullable=True)
    blocked_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    block_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Аудит
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Связи
    roles = relationship("Role", secondary="users_roles", back_populates="users")
    projects = relationship("Project", secondary="user_projects", back_populates="users")
    department = relationship("Department", back_populates="users")
    blocked_by_user = relationship("User", remote_side=[user_id], foreign_keys=[blocked_by])
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    
    # Индексы (объявляются в __table_args__)
    __table_args__ = (
        Index("idx_users_gender", "gender"),
        Index("idx_users_birth_date", "birth_date"),
        Index("idx_users_dept_code", "dept_code"),
        Index("idx_users_status", "status"),
        Index("idx_users_status_username", "status", "user_name"),
        Index("idx_users_blocked_at", "blocked_at", postgresql_where=(status == "blocked")),
        Index("idx_users_last_login", "last_login_at"),
        Index("idx_users_dept_status", "dept_code", "status"),
    )
    
    @property
    def is_active(self) -> bool:
        """Проверка активности пользователя"""
        return self.status == "active"
    
    @property
    def is_blocked(self) -> bool:
        """Проверка блокировки"""
        return self.status == "blocked"
    
    def can_login(self) -> bool:
        """Может ли пользователь войти"""
        return self.status == "active"
