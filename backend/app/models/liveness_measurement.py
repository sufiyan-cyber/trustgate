"""Liveness Measurement database model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class LivenessMeasurement(Base):
    __tablename__ = "liveness_measurements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("verification_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    pulse_detected = Column(Boolean, nullable=False, default=False)
    signal_quality = Column(Float, nullable=False, default=0.0)
    bpm = Column(Float, nullable=True)
    duration_ms = Column(Integer, nullable=False, default=0)
    stable_measurement = Column(Boolean, nullable=False, default=False)
    waveform_quality = Column(Float, nullable=True, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    session = relationship("VerificationSession", back_populates="liveness_measurements")
