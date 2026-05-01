# app/models/refresh_token.py
from sqlalchemy import Column, String, BigInteger, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    token_hash = Column(String(255), primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    revoked = Column(Boolean, nullable=False, default=False)
    
    # Связи
    user = relationship("User", back_populates="refresh_tokens")
    
    __table_args__ = (
        Index("idx_refresh_tokens_expires_at", "expires_at", postgresql_where=(revoked == False)),
        Index("idx_refresh_tokens_user_id", "user_id"),
    )
