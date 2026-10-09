# app/schemas/position.py
from pydantic import BaseModel
from datetime import datetime


class PositionResponse(BaseModel):
    position_id: int
    position_code: str
    position_name_en: str
    position_name_ru: str
    created_at: datetime

    class Config:
        from_attributes = True


class PositionBrief(BaseModel):
    position_id: int
    position_code: str
    position_name_ru: str

    class Config:
        from_attributes = True
