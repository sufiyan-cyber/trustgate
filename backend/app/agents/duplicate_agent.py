"""Duplicate / Reused ID Detection Agent."""
import logging
from typing import Any, Dict
from sqlalchemy.orm import Session
from app.agents.base_agent import BaseAgent
from app.schemas.evidence import AgentResult, AgentStatus, Decision, Severity
from app.models import IdentityDocument, Registration, Participant
from app.core.security import normalize_name, hash_id_number

logger = logging.getLogger("trustgate.duplicate_agent")

class DuplicateDetectionAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="duplicate_detection")

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        db: Session = context.get("db")
        id_number_hash = context.get("id_number_hash")
        id_number_raw = context.get("id_number")
        current_name = context.get("current_name", "")
        current_session_id = context.get("session_id")
        demo_duplicate = context.get("demo_duplicate")

        # 1. Check Demo Override first
        if demo_duplicate:
            dup_detected = demo_duplicate.get("duplicate_detected", False)
            conflict = demo_duplicate.get("conflict_type", "NONE")
            prev_count = demo_duplicate.get("previous_registrations", 0)
            prev_owner = demo_duplicate.get("previous_participant_name", "Unknown")

            if dup_detected:
                return AgentResult(
                    agent=self.name,
                    status=AgentStatus.SUCCESS,
                    decision=Decision.REVIEW,
                    confidence=0.98,
                    severity=Severity.HIGH,
                    reasons=[
                        f"DUPLICATE DETECTED: This ID number was previously registered under '{prev_owner}'.",
                        f"Conflict Type: {conflict}. Current participant name does not match previous record."
                    ],
                    signals={
                        "duplicate_detected": True,
                        "conflict_type": conflict,
                        "previous_registrations": prev_count,
                        "previous_owner": prev_owner
                    }
                )
            else:
                return AgentResult(
                    agent=self.name,
                    status=AgentStatus.SUCCESS,
                    decision=Decision.PASS,
                    confidence=0.96,
                    severity=Severity.LOW,
                    reasons=["No duplicate or reused registrations found for this document."],
                    signals={"duplicate_detected": False, "conflict_type": "NONE", "previous_registrations": 0}
                )

        if not id_number_hash and id_number_raw:
            id_number_hash = hash_id_number(id_number_raw)

        if not id_number_hash or not db:
            return AgentResult(
                agent=self.name,
                status=AgentStatus.SUCCESS,
                decision=Decision.PASS,
                confidence=0.85,
                severity=Severity.LOW,
                reasons=["No prior registration conflict found (unhashed/unindexed document)."],
                signals={"duplicate_detected": False, "conflict_type": "NONE", "previous_registrations": 0}
            )

        # 2. Database query for matching document hash
        matches = (
            db.query(IdentityDocument, Registration, Participant)
            .join(Registration, IdentityDocument.registration_id == Registration.id)
            .join(Participant, Registration.participant_id == Participant.id)
            .filter(IdentityDocument.document_number_hash == id_number_hash)
            .all()
        )

        if not matches:
            return AgentResult(
                agent=self.name,
                status=AgentStatus.SUCCESS,
                decision=Decision.PASS,
                confidence=0.97,
                severity=Severity.LOW,
                reasons=["No prior registrations detected for this ID document."],
                signals={
                    "duplicate_detected": False,
                    "conflict_type": "NONE",
                    "previous_registrations": 0
                }
            )

        # Evaluate matches
        current_norm = normalize_name(current_name)
        reused_diff_name = False
        previous_owners = []

        for doc, reg, part in matches:
            prev_norm = normalize_name(part.name)
            previous_owners.append(part.name)
            if current_norm and prev_norm != current_norm:
                reused_diff_name = True

        if reused_diff_name:
            reasons = [
                f"REUSED ID DETECTED: This ID document was previously registered under participant '{previous_owners[0]}'.",
                f"Identity mismatch with current registrant '{current_name}'. Flagged for administrative verification."
            ]
            return AgentResult(
                agent=self.name,
                status=AgentStatus.SUCCESS,
                decision=Decision.REVIEW,
                confidence=0.98,
                severity=Severity.HIGH,
                reasons=reasons,
                signals={
                    "duplicate_detected": True,
                    "conflict_type": "ID_REUSED_WITH_DIFFERENT_NAME",
                    "previous_registrations": len(matches),
                    "previous_owner": previous_owners[0]
                }
            )
        else:
            reasons = [
                f"ID previously verified for participant '{current_name}' (Repeat scan/check-in).",
                "No conflicting identities detected."
            ]
            return AgentResult(
                agent=self.name,
                status=AgentStatus.SUCCESS,
                decision=Decision.PASS,
                confidence=0.95,
                severity=Severity.LOW,
                reasons=reasons,
                signals={
                    "duplicate_detected": False,
                    "conflict_type": "REPEAT_VERIFICATION",
                    "previous_registrations": len(matches),
                    "previous_owner": current_name
                }
            )
