# app/models/role.py
from sqlalchemy import Column, Integer, BigInteger, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

# Ассоциативная таблица для связи many-to-many между User и Role
users_roles = Table(
    "users_roles",
    Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True),
)

class Role(Base):
    __tablename__ = "roles"
    
    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_title = Column(String(50), nullable=False, unique=True)
    
    # Связи
    users = relationship("User", secondary=users_roles, back_populates="roles")
