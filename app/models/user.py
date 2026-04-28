from sqlalchemy import String, Boolean, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.utils.hasher import hash_password

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(128))  # bcrypt
    role: Mapped[str] = mapped_column(String(20), default="user")  # "admin" или "user"
    projects: Mapped[str] = mapped_column(String(500), default="[]")  # JSON список проектов, например "["proj1", "proj2"]"
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
