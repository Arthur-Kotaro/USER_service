# app/models/token_blacklist.py
from sqlalchemy import Column, UUID, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    token_jti = Column(UUID, primary_key=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index("idx_blacklist_expires_at", "expires_at"),
    )
