"""Review Action database model for audit trail."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class ReviewAction(Base):
    __tablename__ = "review_actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("verification_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer = Column(String(100), nullable=False, default="admin")
    action = Column(String(50), nullable=False)  # APPROVE, REJECT
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    session = relationship("VerificationSession", back_populates="review_actions")
