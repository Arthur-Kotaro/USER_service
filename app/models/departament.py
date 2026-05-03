# app/models/departament.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Department(Base):
    __tablename__ = "departament"
    
    dept_code = Column(String(20), primary_key=True)
    dept_name = Column(String(200), nullable=False, unique=True)
    parent_dept_code = Column(String(20), ForeignKey("departament.dept_code"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Связи
    parent = relationship("Department", remote_side=[dept_code], backref="children")
    users = relationship("User", back_populates="department")
