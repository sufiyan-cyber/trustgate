"""Dashboard metrics and summary statistics API endpoints."""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import VerificationSession, Registration, Participant
from app.services.device_bridge import device_bridge

logger = logging.getLogger("trustgate.dashboard_router")

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Computes high-level metrics for the operator dashboard."""
    # Exclude demo sessions from production operational stats where desired, or include summary
    total_sessions = db.query(func.count(VerificationSession.id)).scalar() or 0
    passed_sessions = db.query(func.count(VerificationSession.id)).filter(VerificationSession.decision == "PASS").scalar() or 0
    review_sessions = db.query(func.count(VerificationSession.id)).filter(VerificationSession.decision == "REVIEW").scalar() or 0
    failed_sessions = db.query(func.count(VerificationSession.id)).filter(VerificationSession.decision == "FAIL").scalar() or 0

    pass_rate = round((passed_sessions / total_sessions * 100), 1) if total_sessions > 0 else 0.0

    # Retrieve 10 most recent sessions
    recent_db_sessions = (
        db.query(VerificationSession)
        .order_by(VerificationSession.started_at.desc())
        .limit(10)
        .all()
    )

    recent_sessions = []
    for s in recent_db_sessions:
        part_name = "Walk-in Participant"
        if s.registration_id:
            reg = db.query(Registration).filter(Registration.id == s.registration_id).first()
            if reg:
                part = db.query(Participant).filter(Participant.id == reg.participant_id).first()
                if part:
                    part_name = part.name

        recent_sessions.append({
            "id": s.id,
            "device_id": s.device_id,
            "status": s.status,
            "decision": s.decision,
            "confidence": s.confidence,
            "risk_level": s.risk_level,
            "participant_name": part_name,
            "is_demo": s.is_demo,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None
        })

    return {
        "metrics": {
            "total_verifications": total_sessions,
            "passed_count": passed_sessions,
            "review_count": review_sessions,
            "failed_count": failed_sessions,
            "pass_rate_pct": pass_rate,
            "active_devices": 1 if device_bridge.state["online"] else 0
        },
        "hardware_status": device_bridge.get_status(),
        "recent_sessions": recent_sessions
    }
