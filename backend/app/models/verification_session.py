"""Verification Session database model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class VerificationSession(Base):
    __tablename__ = "verification_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    registration_id = Column(String(36), ForeignKey("registrations.id", ondelete="SET NULL"), nullable=True, index=True)
    device_id = Column(String(50), nullable=False, default="TG-001", index=True)
    status = Column(String(50), nullable=False, default="IN_PROGRESS", index=True)  # IN_PROGRESS, COMPLETED, FAILED
    decision = Column(String(50), nullable=False, default="PENDING", index=True)   # PASS, REVIEW, FAIL, PENDING
    confidence = Column(Float, nullable=False, default=0.0)
    risk_level = Column(String(50), nullable=False, default="LOW")                 # LOW, MEDIUM, HIGH
    reasons = Column(JSON, nullable=False, default=list)                           # List of explainable human-readable strings
    is_demo = Column(Boolean, default=False, index=True)
    current_command_id = Column(String(36), nullable=True)                        # Unique command ID for hardware safety & anti-replay
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    registration = relationship("Registration", back_populates="verification_sessions")
    evidence = relationship("VerificationEvidence", back_populates="session", cascade="all, delete-orphan")
    liveness_measurements = relationship("LivenessMeasurement", back_populates="session", cascade="all, delete-orphan")
    review_actions = relationship("ReviewAction", back_populates="session", cascade="all, delete-orphan")
