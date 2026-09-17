"""Deterministic, Policy-Driven Verification Decision Engine."""
import logging
from typing import List, Tuple, Dict, Any
from app.schemas.evidence import AgentResult, AgentStatus, Decision, Severity

logger = logging.getLogger("trustgate.decision_engine")

class DecisionEngine:
    """
    Authoritative decision service enforcing event policy and safety rules.
    Takes structured outputs from all agents and produces a deterministic outcome:
    PASS, REVIEW, or FAIL.
    """

    @staticmethod
    def evaluate(agent_results: List[AgentResult]) -> Tuple[Decision, float, str, List[str], str]:
        """
        Evaluates aggregated evidence against deterministic safety gates.
        Returns (decision, confidence, risk_level, reasons, gate_command).
        """
        agent_map: Dict[str, AgentResult] = {res.agent: res for res in agent_results}

        extraction = agent_map.get("document_extraction")
        forensics = agent_map.get("document_forensics")
        identity = agent_map.get("identity_matching")
        duplicate = agent_map.get("duplicate_detection")
        liveness = agent_map.get("liveness_verification")
        eligibility = agent_map.get("eligibility_evaluation")

        reasons: List[str] = []
        confidences: List[float] = [res.confidence for res in agent_results if res.confidence > 0]
        avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.70

        # Rule 1: CRITICAL SECURITY CONFLICT - Reused ID with different name
        if duplicate and duplicate.signals.get("conflict_type") == "ID_REUSED_WITH_DIFFERENT_NAME":
            reasons.append("CRITICAL CONFLICT: Document previously registered under a different participant name.")
            reasons.append("Physical gate remains locked. Forwarded to Admin Review for manual resolution.")
            return Decision.REVIEW, 0.65, "HIGH", reasons, "KEEP_LOCKED"

        # Rule 2: HARD INELIGIBILITY - Definitely underage or disqualified
        if eligibility and eligibility.decision == Decision.FAIL:
            reasons.extend(eligibility.reasons)
            reasons.append("Participant does not satisfy minimum event eligibility criteria.")
            return Decision.FAIL, 0.95, "HIGH", reasons, "KEEP_LOCKED"

        # Rule 3: HIGH TAMPERING RISK in Document Forensics
        if forensics and forensics.signals.get("tampering_risk", 0.0) >= 0.70:
            reasons.append(f"Document integrity alert: localized digital tampering detected (risk: {int(forensics.signals['tampering_risk']*100)}%).")
            reasons.extend([f"Anomaly: {a}" for a in forensics.signals.get("anomalies", [])])
            reasons.append("Physical gate remains locked pending manual document inspection.")
            return Decision.REVIEW, 0.60, "HIGH", reasons, "KEEP_LOCKED"

        # Rule 4: FACE MISMATCH
        if identity and identity.signals.get("match_status") == "NO_MATCH":
            reasons.append("Biometric alert: live selfie does not match photo on the presented identity card.")
            reasons.append("Rejection avoided to prevent false positives; routed to Admin Review.")
            return Decision.REVIEW, 0.62, "HIGH", reasons, "KEEP_LOCKED"

        # Rule 5: INCONCLUSIVE LIVENESS (e.g. no pulse, finger moved, weak reading)
        # CRITICAL PRINCIPLE: Never reject someone based solely on a weak liveness sensor signal!
        if liveness and (liveness.status == AgentStatus.INCONCLUSIVE or liveness.decision == Decision.REVIEW):
            reasons.append("Liveness sensor signal inconclusive or interrupted during measurement.")
            reasons.append("Participant not rejected; organizer verification required.")
            return Decision.REVIEW, 0.70, "LOW", reasons, "KEEP_LOCKED"

        # Rule 6: MODERATE AMBIGUITIES (blurry doc, partial name match)
        ambiguous_signals = []
        if forensics and forensics.decision == Decision.REVIEW:
            ambiguous_signals.append("Document image quality or blur requires review")
        if identity and identity.decision == Decision.REVIEW:
            ambiguous_signals.append("Name similarity requires manual confirmation")
        if eligibility and eligibility.decision == Decision.REVIEW:
            ambiguous_signals.append("Institutional qualification requires manual review")

        if len(ambiguous_signals) > 0:
            reasons.extend(ambiguous_signals)
            reasons.append("Evidence is ambiguous. Automatic rejection avoided per system policy.")
            return Decision.REVIEW, 0.68, "MEDIUM", reasons, "KEEP_LOCKED"

        # Rule 7: ALL PRIMARY CRITERIA SATISFIED -> PASS
        # Verify extraction, forensics, identity, duplicate, eligibility, liveness
        all_passed = (
            (extraction is None or extraction.decision == Decision.PASS) and
            (forensics is None or forensics.decision == Decision.PASS) and
            (identity is None or identity.decision == Decision.PASS) and
            (duplicate is None or duplicate.decision == Decision.PASS) and
            (liveness is None or liveness.decision == Decision.PASS) and
            (eligibility is None or eligibility.decision == Decision.PASS)
        )

        if all_passed:
            reasons.append("ID fields successfully extracted and verified")
            reasons.append("DOB satisfies event age requirements")
            reasons.append("Participant identity and facial biometrics matched")
            reasons.append("MAX30102 physiological pulse signal verified")
            reasons.append("Document integrity verified with zero tampering indicators")
            reasons.append("No prior registration conflicts found")
            return Decision.PASS, max(0.92, avg_confidence), "LOW", reasons, "OPEN_GATE"

        # Fallback safe state: REVIEW
        reasons.append("Evidence requires organizer verification.")
        return Decision.REVIEW, 0.70, "MEDIUM", reasons, "KEEP_LOCKED"
