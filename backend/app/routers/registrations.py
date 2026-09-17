"""Registrations and participants management API endpoints."""
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Participant, Registration, IdentityDocument, VerificationSession
from app.schemas.registration import RegistrationResponse, ParticipantCreate
from app.core.security import hash_id_number

logger = logging.getLogger("trustgate.registrations_router")

router = APIRouter(prefix="/api/registrations", tags=["Registrations"])

@router.get("", response_model=List[RegistrationResponse])
async def list_registrations(
    status: Optional[str] = Query(None, description="Filter by status: REGISTERED, VERIFIED, FLAGGED, REJECTED"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    db: Session = Depends(get_db)
):
    """Retrieves all registrations with associated participant profiles."""
    query = db.query(Registration).join(Participant, Registration.participant_id == Participant.id)

    if status:
        query = query.filter(Registration.status == status)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter((Participant.name.ilike(search_pattern)) | (Participant.email.ilike(search_pattern)))

    registrations = query.order_by(Registration.created_at.desc()).all()
    return registrations

@router.get("/{registration_id}", response_model=RegistrationResponse)
async def get_registration(registration_id: str, db: Session = Depends(get_db)):
    """Retrieves specific registration details."""
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
    return reg

@router.post("", response_model=RegistrationResponse)
async def create_registration(req: ParticipantCreate, event_id: str = "hackingly-hackathon-2026", db: Session = Depends(get_db)):
    """Creates a new participant registration."""
    # Check existing email
    existing_part = db.query(Participant).filter(Participant.email == req.email).first()
    if existing_part:
        participant = existing_part
    else:
        participant = Participant(
            id=str(uuid.uuid4()),
            name=req.name,
            email=req.email,
            phone=req.phone,
            institution=req.institution,
            created_at=datetime.now(timezone.utc)
        )
        db.add(participant)
        db.flush()

    registration = Registration(
        id=str(uuid.uuid4()),
        participant_id=participant.id,
        event_id=event_id,
        status="REGISTERED",
        created_at=datetime.now(timezone.utc)
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)

    return registration
