# app/schemas/impersonation.py
from pydantic import BaseModel, Field


class ImpersonateRequest(BaseModel):
    donor_id: int = Field(..., gt=0)


class ImpersonateResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    impersonation_id: str
    recipient_id: int
    donor_id: int
    expires_in: int


class ImpersonationCloseRequest(BaseModel):
    impersonation_id: str
