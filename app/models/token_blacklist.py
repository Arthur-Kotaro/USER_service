# app/models/token_blacklist.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    token_jti = Column(String(255), primary_key=True)  # JWT ID
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
