# app/models/position.py
from sqlalchemy import Column, SmallInteger, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Position(Base):
    __tablename__ = "positions"

    position_id = Column(SmallInteger, primary_key=True, autoincrement=True)
    position_code = Column(String(50), unique=True, nullable=False, index=True)
    position_name_en = Column(String(100), nullable=False)
    position_name_ru = Column(String(100), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<Position(code={self.position_code}, name_ru={self.position_name_ru})>"
