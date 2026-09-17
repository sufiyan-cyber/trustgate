"""Verification Evidence database model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class VerificationEvidence(Base):
    __tablename__ = "verification_evidence"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("verification_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="SUCCESS")     # SUCCESS, INCONCLUSIVE, ERROR
    decision = Column(String(50), nullable=False, default="PASS")       # PASS, REVIEW, FAIL
    confidence = Column(Float, nullable=False, default=0.0)
    severity = Column(String(50), nullable=False, default="LOW")        # LOW, MEDIUM, HIGH
    reason = Column(Text, nullable=True)
    raw_output = Column(JSON, nullable=False, default=dict)             # Granular signals and agent parameters
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    session = relationship("VerificationSession", back_populates="evidence")
