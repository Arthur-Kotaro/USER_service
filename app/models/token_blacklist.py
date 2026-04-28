class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(String(50), unique=True)  # JWT ID (уникальный идентификатор токена)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
