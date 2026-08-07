# app/models/login_history.py (НОВЫЙ ФАЙЛ)
from sqlalchemy import Column, BigInteger, String, DateTime, Index
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.sql import func
from app.database import Base


class LoginHistory(Base):
    __tablename__ = "login_history"
    
    login_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True)  # NULL = пользователь не найден
    login_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ip_address = Column(INET, nullable=True)
    user_agent = Column(String, nullable=True)
    login_status = Column(String(20), nullable=False)  # success, failed, expired, blocked
    failure_reason = Column(String, nullable=True)
    session_id = Column(UUID(as_uuid=True), nullable=True)
    
    __table_args__ = (
        Index("idx_login_history_user_id", "user_id"),
        Index("idx_login_history_login_at", "login_at"),
        Index("idx_login_history_status", "login_status"),
        Index("idx_login_history_user_status", "user_id", "login_status"),
    )
    
    def __repr__(self):
        return f"<LoginHistory(login_id={self.login_id}, user_id={self.user_id}, status='{self.login_status}')>"
