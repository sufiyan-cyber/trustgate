"""Identity Document database model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class IdentityDocument(Base):
    __tablename__ = "identity_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    registration_id = Column(String(36), ForeignKey("registrations.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False, default="COLLEGE_ID")  # COLLEGE_ID, GOVERNMENT_ID, PASSPORT
    document_number_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash for privacy & fast duplicate lookup
    name = Column(String(255), nullable=True)
    dob = Column(String(50), nullable=True)
    institution = Column(String(255), nullable=True)
    image_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    registration = relationship("Registration", back_populates="identity_documents")
