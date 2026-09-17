"""Registration database model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Registration(Base):
    __tablename__ = "registrations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    participant_id = Column(String(36), ForeignKey("participants.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(100), nullable=False, default="hackingly-hackathon-2026", index=True)
    status = Column(String(50), nullable=False, default="REGISTERED", index=True)  # REGISTERED, VERIFIED, FLAGGED, REJECTED
    is_demo = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    participant = relationship("Participant", back_populates="registrations")
    identity_documents = relationship("IdentityDocument", back_populates="registration", cascade="all, delete-orphan")
    verification_sessions = relationship("VerificationSession", back_populates="registration", cascade="all, delete-orphan")
