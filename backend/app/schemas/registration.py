"""Pydantic schemas for participants and registrations."""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

class ParticipantBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    institution: Optional[str] = None

class ParticipantCreate(ParticipantBase):
    pass

class ParticipantResponse(ParticipantBase):
    id: str
    is_demo: bool
    created_at: datetime

    class Config:
        from_attributes = True

class IdentityDocumentResponse(BaseModel):
    id: str
    document_type: str
    document_number_hash: str
    name: Optional[str]
    dob: Optional[str]
    institution: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class RegistrationResponse(BaseModel):
    id: str
    participant_id: str
    event_id: str
    status: str
    is_demo: bool
    created_at: datetime
    participant: Optional[ParticipantResponse] = None
    identity_documents: List[IdentityDocumentResponse] = []

    class Config:
        from_attributes = True
