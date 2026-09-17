"""Dependency-Aware Verification Orchestrator executing the multi-agent DAG pipeline."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.orm import Session
from app.agents import (
    ExtractionAgent,
    DocumentForensicsAgent,
    IdentityMatchingAgent,
    DuplicateDetectionAgent,
    LivenessAgent,
    EligibilityAgent,
    DecisionAgent
)
from app.schemas.evidence import AgentResult, AgentStatus, Decision, Severity
from app.models import VerificationSession, VerificationEvidence, Registration, Participant
from app.core.image_utils import assess_image_quality

logger = logging.getLogger("trustgate.orchestrator")

class VerificationOrchestrator:
    """
    Coordinates the execution of the Trust Gate AI verification pipeline.
    Enforces strict dependency order:
    1. Image Quality Check
    2. ExtractionAgent (AWS Textract primary)
    3. DocumentForensicsAgent (concurrent)
    4. IdentityMatchingAgent (consumes extracted fields + photo)
    5. DuplicateDetectionAgent (consumes extracted ID hash)
    6. LivenessAgent (consumes MAX30102 pulse telemetry)
    7. EligibilityAgent (consumes extracted DOB & ID type)
    8. DecisionAgent (synthesizes structured evidence into final verdict)
    """

    def __init__(self):
        self.extraction_agent = ExtractionAgent()
        self.forensics_agent = DocumentForensicsAgent()
        self.identity_agent = IdentityMatchingAgent()
        self.duplicate_agent = DuplicateDetectionAgent()
        self.liveness_agent = LivenessAgent()
        self.eligibility_agent = EligibilityAgent()
        self.decision_agent = DecisionAgent()

    async def run_pipeline(
        self,
        session_id: str,
        db: Session,
        id_image_bytes: Optional[bytes] = None,
        selfie_image_bytes: Optional[bytes] = None,
        liveness_data: Optional[Dict[str, Any]] = None,
        demo_overrides: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes the verification DAG and records evidence to the database.
        Streams step-by-step progress via progress_callback if provided.
        """
        logger.info("Starting verification pipeline for session: %s", session_id)
        
        session = db.query(VerificationSession).filter(VerificationSession.id == session_id).first()
        if not session:
            raise ValueError(f"Verification session {session_id} not found")

        # Load registration data if present
        reg = None
        part = None
        if session.registration_id:
            reg = db.query(Registration).filter(Registration.id == session.registration_id).first()
            if reg:
                part = db.query(Participant).filter(Participant.id == reg.participant_id).first()

        reg_name = part.name if part else ""
        reg_dob = ""
        agent_results: List[AgentResult] = []

        async def notify(stage: str, status: str, details: Dict[str, Any]):
            if progress_callback:
                try:
                    msg = {
                        "type": "PIPELINE_PROGRESS",
                        "session_id": session_id,
                        "stage": stage,
                        "status": status,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "details": details
                    }
                    if asyncio.iscoroutinefunction(progress_callback):
                        await progress_callback(msg)
                    else:
                        progress_callback(msg)
                except Exception as ex:
                    logger.debug("Progress callback exception: %s", ex)

        # -------------------------------------------------------------
        # Step 1: Pre-Extraction Image Quality & Blur Validation
        # -------------------------------------------------------------
        await notify("IMAGE_QUALITY_CHECK", "IN_PROGRESS", {"label": "Validating document image clarity"})
        if id_image_bytes:
            quality_score, q_signals = assess_image_quality(id_image_bytes)
            if q_signals.get("is_blurry", False):
                logger.warning("Document image blur detected (sharpness: %s)", q_signals.get("sharpness_var"))
            await notify("IMAGE_QUALITY_CHECK", "COMPLETED", {"quality_score": quality_score, "signals": q_signals})
        else:
            await notify("IMAGE_QUALITY_CHECK", "SKIPPED", {"note": "Demo or mock data used"})

        # -------------------------------------------------------------
        # Step 2: Document Extraction Agent (AWS Textract)
        # -------------------------------------------------------------
        await notify("DOCUMENT_EXTRACTION", "IN_PROGRESS", {"label": "Calling AWS Textract document parser"})
        ext_context = {
            "id_image_bytes": id_image_bytes,
            "demo_extraction": demo_overrides.get("document") if demo_overrides else None
        }

        if demo_overrides and demo_overrides.get("document"):
            doc_data = demo_overrides["document"]
            from app.core.security import hash_id_number
            ext_result = AgentResult(
                agent="document_extraction",
                status=AgentStatus.SUCCESS,
                decision=Decision.PASS,
                confidence=0.96,
                severity=Severity.LOW,
                reasons=[f"Document fields extracted: {doc_data.get('name')}, DOB: {doc_data.get('dob')}"],
                signals={
                    "name": doc_data.get("name"),
                    "dob": doc_data.get("dob"),
                    "id_number": doc_data.get("id_number"),
                    "id_number_hash": hash_id_number(doc_data.get("id_number", "")),
                    "id_type": doc_data.get("document_type", "COLLEGE_ID"),
                    "institution": doc_data.get("institution"),
                    "provider_source": "DEMO_SIMULATION"
                }
            )
        else:
            ext_result = await self.extraction_agent.run(ext_context)

        agent_results.append(ext_result)
        self._save_evidence(db, session_id, ext_result)
        await notify("DOCUMENT_EXTRACTION", "COMPLETED", {"result": ext_result.model_dump()})

        extracted_name = ext_result.signals.get("name", "")
        extracted_dob = ext_result.signals.get("dob", "")
        id_number_hash = ext_result.signals.get("id_number_hash", "")
        id_number = ext_result.signals.get("id_number", "")
        institution = ext_result.signals.get("institution", "")
        doc_type = ext_result.signals.get("id_type", "COLLEGE_ID")

        # Fallback registration name to extracted name if no participant pre-registered
        if not reg_name:
            reg_name = extracted_name

        # -------------------------------------------------------------
        # Steps 3, 4, 5, 6, 7: Dependent Agents Executed Concurrently
        # -------------------------------------------------------------
        await notify("EVALUATION_AGENTS", "IN_PROGRESS", {"label": "Running forensics, identity, duplicate, eligibility, and liveness"})

        # Contexts for dependent agents
        forensics_ctx = {
            "id_image_bytes": id_image_bytes,
            "extracted_data": ext_result.signals,
            "demo_anomaly": demo_overrides.get("forensics") if demo_overrides else None
        }
        identity_ctx = {
            "registration_name": reg_name,
            "extracted_name": extracted_name,
            "registration_dob": reg_dob,
            "extracted_dob": extracted_dob,
            "id_image_bytes": id_image_bytes,
            "selfie_image_bytes": selfie_image_bytes,
            "demo_identity": demo_overrides.get("identity") if demo_overrides else None
        }
        duplicate_ctx = {
            "db": db,
            "id_number_hash": id_number_hash,
            "id_number": id_number,
            "current_name": extracted_name or reg_name,
            "session_id": session_id,
            "demo_duplicate": demo_overrides.get("duplicate") if demo_overrides else None
        }
        liveness_ctx = {
            "liveness_data": liveness_data or {},
            "demo_liveness": demo_overrides.get("liveness") if demo_overrides else None
        }
        eligibility_ctx = {
            "extracted_dob": extracted_dob,
            "registration_dob": reg_dob,
            "document_type": doc_type,
            "institution": institution,
            "demo_eligibility": demo_overrides.get("eligibility") if demo_overrides else None
        }

        # Run concurrent dependent tasks
        forensics_res, identity_res, duplicate_res, liveness_res, eligibility_res = await asyncio.gather(
            self.forensics_agent.run(forensics_ctx),
            self.identity_agent.run(identity_ctx),
            self.duplicate_agent.run(duplicate_ctx),
            self.liveness_agent.run(liveness_ctx),
            self.eligibility_agent.run(eligibility_ctx)
        )

        dep_results = [forensics_res, identity_res, duplicate_res, liveness_res, eligibility_res]
        agent_results.extend(dep_results)

        for res in dep_results:
            self._save_evidence(db, session_id, res)
            await notify(res.agent.upper(), "COMPLETED", {"result": res.model_dump()})

        # -------------------------------------------------------------
        # Step 8: Decision Agent (Synthesize & Explain)
        # -------------------------------------------------------------
        await notify("DECISION_SYNTHESIS", "IN_PROGRESS", {"label": "Synthesizing evidence and computing safety verdict"})
        decision_ctx = {"agent_results": agent_results}
        decision_res = await self.decision_agent.run(decision_ctx)
        self._save_evidence(db, session_id, decision_res)

        final_decision = decision_res.decision
        final_confidence = decision_res.confidence
        risk_level = decision_res.signals.get("risk_level", "LOW")
        gate_command = decision_res.signals.get("gate_command", "KEEP_LOCKED")

        # Update VerificationSession table
        session.status = "COMPLETED"
        session.decision = final_decision.value
        session.confidence = final_confidence
        session.risk_level = risk_level
        session.reasons = decision_res.reasons
        session.completed_at = datetime.now(timezone.utc)
        db.commit()

        await notify("DECISION_SYNTHESIS", "COMPLETED", {
            "decision": final_decision.value,
            "confidence": final_confidence,
            "risk_level": risk_level,
            "gate_command": gate_command,
            "reasons": decision_res.reasons
        })

        return {
            "session_id": session_id,
            "decision": final_decision,
            "confidence": final_confidence,
            "risk_level": risk_level,
            "reasons": decision_res.reasons,
            "gate_command": gate_command,
            "agent_results": agent_results,
            "completed_at": session.completed_at
        }

    def _save_evidence(self, db: Session, session_id: str, res: AgentResult):
        """Persists agent result record into verification_evidence table."""
        try:
            primary_reason = res.reasons[0] if res.reasons else None
            evidence = VerificationEvidence(
                session_id=session_id,
                agent_name=res.agent,
                status=res.status.value,
                decision=res.decision.value,
                confidence=res.confidence,
                severity=res.severity.value,
                reason=primary_reason,
                raw_output={
                    "reasons": res.reasons,
                    "signals": res.signals
                }
            )
            db.add(evidence)
            db.commit()
        except Exception as e:
            logger.error("Failed to save evidence for %s: %s", res.agent, e)
            db.rollback()
