"""Admin manual review workflow and audit action API endpoints."""
import uuid
import logging
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import VerificationSession, ReviewAction, Registration, Participant, VerificationEvidence
from app.schemas.review import ReviewActionRequest, ReviewActionResponse
from app.services.device_bridge import device_bridge
from app.routers.ws import ws_manager

logger = logging.getLogger("trustgate.review_router")

router = APIRouter(prefix="/api/review", tags=["Admin Review"])

@router.get("/flagged")
async def get_flagged_sessions(db: Session = Depends(get_db)):
    """Retrieves all sessions that require organizer review (decision == REVIEW)."""
    sessions = (
        db.query(VerificationSession)
        .filter(VerificationSession.decision == "REVIEW")
        .order_by(VerificationSession.started_at.desc())
        .all()
    )

    flagged_list = []
    for s in sessions:
        part_name = "Walk-in Participant"
        institution = "N/A"
        email = ""
        if s.registration_id:
            reg = db.query(Registration).filter(Registration.id == s.registration_id).first()
            if reg:
                part = db.query(Participant).filter(Participant.id == reg.participant_id).first()
                if part:
                    part_name = part.name
                    institution = part.institution or "N/A"
                    email = part.email

        # Get evidence
        ev_items = db.query(VerificationEvidence).filter(VerificationEvidence.session_id == s.id).all()
        evidence_summary = {}
        for ev in ev_items:
            evidence_summary[ev.agent_name] = {
                "decision": ev.decision,
                "confidence": ev.confidence,
                "severity": ev.severity,
                "reason": ev.reason,
                "signals": ev.raw_output.get("signals", {}) if ev.raw_output else {}
            }

        flagged_list.append({
            "session_id": s.id,
            "registration_id": s.registration_id,
            "participant_name": part_name,
            "institution": institution,
            "email": email,
            "device_id": s.device_id,
            "decision": s.decision,
            "confidence": s.confidence,
            "risk_level": s.risk_level,
            "reasons": s.reasons,
            "is_demo": s.is_demo,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "evidence": evidence_summary
        })

    return flagged_list

@router.post("/{session_id}/approve", response_model=ReviewActionResponse)
async def approve_session(
    session_id: str,
    req: ReviewActionRequest,
    db: Session = Depends(get_db)
):
    """
    Organizer manual override: APPROVES the session.
    Logs immutable audit record, marks registration VERIFIED, and issues authoritative gate open.
    """
    session = db.query(VerificationSession).filter(VerificationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Verification session not found")

    # 1. Record Audit Action
    action = ReviewAction(
        id=str(uuid.uuid4()),
        session_id=session_id,
        reviewer=req.reviewer,
        action="APPROVE",
        reason=req.reason,
        created_at=datetime.now(timezone.utc)
    )
    db.add(action)

    # 2. Update Session Decision to PASS
    session.decision = "PASS"
    session.risk_level = "LOW"
    session.reasons = session.reasons + [f"✓ Manually approved by organizer '{req.reviewer}': {req.reason}"]

    # 3. Update Registration if linked
    if session.registration_id:
        reg = db.query(Registration).filter(Registration.id == session.registration_id).first()
        if reg:
            reg.status = "VERIFIED"

    db.commit()

    # 4. Command Physical Servo Gate to Open
    logger.info("Admin approved session %s. Dispatching OPEN_GATE...", session_id)
    opened, policy_reason = device_bridge.request_gate_open(session_id)
    if opened:
        device_bridge.set_lcd_state("ACCESS_GRANTED", "Manual Override Approved")
    else:
        logger.warning("Hardware command failed after approval: %s", policy_reason)

    await ws_manager.broadcast({
        "type": "ADMIN_REVIEW_ACTION",
        "session_id": session_id,
        "action": "APPROVE",
        "reviewer": req.reviewer,
        "reason": req.reason,
        "timestamp": action.created_at.isoformat()
    })

    return action

@router.post("/{session_id}/reject", response_model=ReviewActionResponse)
async def reject_session(
    session_id: str,
    req: ReviewActionRequest,
    db: Session = Depends(get_db)
):
    """
    Organizer manual override: REJECTS the session.
    Logs immutable audit record, marks registration REJECTED, and keeps gate locked.
    """
    session = db.query(VerificationSession).filter(VerificationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Verification session not found")

    action = ReviewAction(
        id=str(uuid.uuid4()),
        session_id=session_id,
        reviewer=req.reviewer,
        action="REJECT",
        reason=req.reason,
        created_at=datetime.now(timezone.utc)
    )
    db.add(action)

    session.decision = "FAIL"
    session.risk_level = "HIGH"
    session.reasons = session.reasons + [f"✕ Manually rejected by organizer '{req.reviewer}': {req.reason}"]

    if session.registration_id:
        reg = db.query(Registration).filter(Registration.id == session.registration_id).first()
        if reg:
            reg.status = "REJECTED"

    db.commit()

    device_bridge.set_lcd_state("VERIFICATION_FAILED", "Manual Review Rejected")
    device_bridge.send_command({"command": "LOCK_GATE"})

    await ws_manager.broadcast({
        "type": "ADMIN_REVIEW_ACTION",
        "session_id": session_id,
        "action": "REJECT",
        "reviewer": req.reviewer,
        "reason": req.reason,
        "timestamp": action.created_at.isoformat()
    })

    return action
