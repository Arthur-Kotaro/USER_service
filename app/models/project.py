# app/models/project.py
from sqlalchemy import Column, Integer, String, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

# Таблица связи user_projects
user_projects_table = Table(
    "user_projects",
    Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("project_id", Integer, ForeignKey("projects.project_id", ondelete="CASCADE"), primary_key=True)
)

class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(Integer, primary_key=True, autoincrement=True)
    project_title = Column(String(100), unique=True, nullable=False)
    project_description = Column(Text, nullable=True)
    
    # Связи
    users = relationship("User", secondary="user_projects", back_populates="projects")
