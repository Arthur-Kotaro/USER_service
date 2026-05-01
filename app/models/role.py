# app/models/role.py
from sqlalchemy import Column, SmallInteger, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

# Таблица связи users_roles
users_roles_table = Table(
    "users_roles",
    Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", SmallInteger, ForeignKey("roles.role_id", ondelete="RESTRICT"), primary_key=True)
)

class Role(Base):
    __tablename__ = "roles"
    
    role_id = Column(SmallInteger, primary_key=True, autoincrement=False)
    role_title = Column(String(50), unique=True, nullable=False)
    
    # Связи
    users = relationship("User", secondary="users_roles", back_populates="roles")
