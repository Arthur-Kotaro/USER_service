# app/models/project.py
from sqlalchemy import Column, Integer, BigInteger, String, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

# Ассоциативная таблица для связи many-to-many между User и Project
user_projects = Table(
    "user_projects",
    Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("project_id", Integer, ForeignKey("projects.project_id", ondelete="CASCADE"), primary_key=True),
)

class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(Integer, primary_key=True, autoincrement=True)
    project_title = Column(String(100), nullable=False, unique=True)
    project_description = Column(Text, nullable=True)
    
    # Связи
    users = relationship("User", secondary=user_projects, back_populates="projects")
