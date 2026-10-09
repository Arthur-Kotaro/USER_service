# app/models/department.py
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    dept_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dept_code = Column(String(50), unique=True, nullable=False, index=True)
    dept_name_en = Column(String(200), nullable=False)
    dept_name_ru = Column(String(200), nullable=False)
    parent_dept_id = Column(UUID(as_uuid=True), ForeignKey("departments.dept_id", ondelete="SET NULL"), nullable=True)
    type = Column(String(20), nullable=False)
    level = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    parent = relationship("Department", remote_side=[dept_id], backref="children")
    users = relationship("User", back_populates="department")

    __table_args__ = (
        CheckConstraint(
            "type IN ('division','directorate','department','section','shop','bureau','group','area','store')",
            name="chk_dept_type",
        ),
        CheckConstraint("level BETWEEN 1 AND 6", name="chk_dept_level"),
        Index("idx_dept_parent", "parent_dept_id"),
        Index("idx_dept_type", "type"),
        Index("idx_dept_level", "level"),
    )

    def __repr__(self):
        return f"<Department(code={self.dept_code}, name_ru={self.dept_name_ru})>"
