# app/models/department.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import List, Optional
from app.database import Base

class Department(Base):
    __tablename__ = "departament"
    
    dept_code = Column(String(20), primary_key=True)
    dept_name = Column(String(200), unique=True, nullable=False)
    parent_dept_code = Column(String(20), ForeignKey("departament.dept_code"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Связи
    users = relationship("User", back_populates="department")
    children = relationship("Department", backref="parent", remote_side=[dept_code])
