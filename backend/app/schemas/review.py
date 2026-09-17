"""Pydantic schemas for admin review actions and audit trails."""
from datetime import datetime
from pydantic import BaseModel, Field

class ReviewActionRequest(BaseModel):
    reviewer: str = Field(default="admin", description="Username of the reviewing organizer")
    reason: str = Field(min_length=3, description="Audit justification for manual approval or rejection")

class ReviewActionResponse(BaseModel):
    id: str
    session_id: str
    reviewer: str
    action: str  # APPROVE, REJECT
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True
