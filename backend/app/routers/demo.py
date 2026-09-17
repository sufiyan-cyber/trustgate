"""Deterministic Demo Mode API endpoints for verified test scenarios A through F."""
import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.demo import DemoRunRequest, DemoRunResponse, DemoScenarioEnum
from app.schemas.evidence import Decision
from app.models import VerificationSession, Participant, Registration, IdentityDocument
from app.core.mock_data import DEMO_SCENARIOS
from app.services.orchestrator import VerificationOrchestrator
from app.services.device_bridge import device_bridge
from app.routers.ws import ws_manager

logger = logging.getLogger("trustgate.demo_router")

router = APIRouter(prefix="/api/demo", tags=["Demo Mode"])

orchestrator = VerificationOrchestrator()

@router.get("/scenarios")
async def list_scenarios():
    """Returns metadata for all 6 deterministic demonstration scenarios."""
    scenarios_list = []
    for key, sc in DEMO_SCENARIOS.items():
        scenarios_list.append({
            "key": key,
            "title": sc["title"],
            "description": sc["description"],
            "expected_decision": sc["expected_decision"],
            "expected_confidence": sc["expected_confidence"],
            "risk_level": sc["risk_level"],
            "gate_action": sc["gate_action"]
        })
    return scenarios_list

@router.post("/run-scenario", response_model=DemoRunResponse)
async def run_demo_scenario(req: DemoRunRequest, db: Session = Depends(get_db)):
    """
    Executes a deterministic demo scenario (A, B, C, D, E, or F).
    Isolated with is_demo: true.
    Demonstrates multi-agent execution trace and physical servo actuation safely.
    """
    scenario_key = req.scenario.value
    if scenario_key not in DEMO_SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Unknown scenario key '{scenario_key}'")

    sc_config = DEMO_SCENARIOS[scenario_key]
    part_data = sc_config["participant"]

    logger.info("Executing DEMO MODE %s: '%s'", scenario_key, sc_config["title"])

    # 1. Create or fetch isolated Demo Participant
    demo_part = db.query(Participant).filter(Participant.email == part_data["email"]).first()
    if not demo_part:
        demo_part = Participant(
            id=str(uuid.uuid4()),
            name=part_data["name"],
            email=part_data["email"],
            phone=part_data.get("phone"),
            institution=part_data.get("institution"),
            is_demo=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(demo_part)
        db.flush()

    # 2. Create Demo Registration
    demo_reg = Registration(
        id=str(uuid.uuid4()),
        participant_id=demo_part.id,
        event_id="hackingly-hackathon-2026",
        status="REGISTERED",
        is_demo=True,
        created_at=datetime.now(timezone.utc)
    )
    db.add(demo_reg)
    db.flush()

    # 3. Create Verification Session marked as DEMO
    session = VerificationSession(
        id=str(uuid.uuid4()),
        registration_id=demo_reg.id,
        device_id=req.device_id,
        status="IN_PROGRESS",
        decision="PENDING",
        confidence=0.0,
        risk_level="LOW",
        reasons=[],
        is_demo=True,
        started_at=datetime.now(timezone.utc)
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # 4. Broadcast Demo Start Event
    await ws_manager.broadcast({
        "type": "DEMO_SCENARIO_STARTED",
        "scenario": scenario_key,
        "title": sc_config["title"],
        "session_id": session.id,
        "is_demo": True
    })

    # 5. Progress Callback for real-time WebSocket agent tracing
    async def broadcast_progress(msg: dict):
        msg["is_demo"] = True
        await ws_manager.broadcast(msg)

    # 6. Run Orchestrator DAG with Scenario Overrides
    result = await orchestrator.run_pipeline(
        session_id=session.id,
        db=db,
        id_image_bytes=None,
        selfie_image_bytes=None,
        liveness_data=sc_config["liveness"],
        demo_overrides=sc_config,
        progress_callback=broadcast_progress
    )

    decision = result["decision"]
    gate_action = result["gate_command"]

    # 7. Hardware Reaction
    if decision == Decision.PASS:
        device_bridge.set_lcd_state("ACCESS_GRANTED", "Demo: Access Granted")
        if req.actuate_hardware:
            device_bridge.request_gate_open(session.id)
    elif decision == Decision.REVIEW:
        device_bridge.set_lcd_state("REVIEW_REQUIRED", "Demo: Review Required")
    else:
        device_bridge.set_lcd_state("VERIFICATION_FAILED", "Demo: Failed")

    await ws_manager.broadcast({
        "type": "DEMO_SCENARIO_COMPLETE",
        "scenario": scenario_key,
        "session_id": session.id,
        "decision": decision.value,
        "confidence": result["confidence"],
        "risk_level": result["risk_level"],
        "gate_action": gate_action,
        "reasons": result["reasons"],
        "is_demo": True
    })

    return DemoRunResponse(
        scenario=scenario_key,
        scenario_title=sc_config["title"],
        scenario_description=sc_config["description"],
        is_demo=True,
        session_id=session.id,
        decision=decision,
        confidence=result["confidence"],
        risk_level=result["risk_level"],
        reasons=result["reasons"],
        gate_action=gate_action,
        agent_results=result["agent_results"]
    )
