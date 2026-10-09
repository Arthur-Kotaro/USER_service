# app/models/role.py
from sqlalchemy import Column, SmallInteger, String, Table, ForeignKey, BigInteger, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


users_roles = Table(
    "users_roles",
    Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", SmallInteger, ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True),
    Column("assigned_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(SmallInteger, primary_key=True, autoincrement=True)
    role_code = Column(String(50), unique=True, nullable=False, index=True)
    role_name_en = Column(String(100), nullable=False)
    role_name_ru = Column(String(100), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    users = relationship("User", secondary=users_roles, back_populates="roles")

    @property
    def display_name(self) -> str:
        return self.role_name_ru or self.role_name_en

    def __repr__(self):
        return f"<Role(code={self.role_code}, name_ru={self.role_name_ru})>"
