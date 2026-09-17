"""Identity Matching Agent comparing registration data and facial embeddings."""
import logging
from difflib import SequenceMatcher
from typing import Any, Dict
from app.agents.base_agent import BaseAgent
from app.schemas.evidence import AgentResult, AgentStatus, Decision, Severity
from app.adapters.face_provider import get_face_provider, MockFaceProvider
from app.core.security import normalize_name
from app.config import settings

logger = logging.getLogger("trustgate.identity_agent")

class IdentityMatchingAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="identity_matching")
        self.face_provider = get_face_provider()

    def _name_similarity(self, name1: str, name2: str) -> float:
        if not name1 or not name2:
            return 0.50
        n1 = normalize_name(name1)
        n2 = normalize_name(name2)
        if n1 == n2:
            return 1.0
        # Check token subset match (e.g. "Rahul Verma" vs "Rahul V")
        tokens1 = set(n1.split())
        tokens2 = set(n2.split())
        if tokens1 and tokens2 and (tokens1.issubset(tokens2) or tokens2.issubset(tokens1)):
            return 0.95
        return round(SequenceMatcher(None, n1, n2).ratio(), 2)

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        reg_name = context.get("registration_name", "")
        extracted_name = context.get("extracted_name", "")
        reg_dob = context.get("registration_dob", "")
        extracted_dob = context.get("extracted_dob", "")
        id_image_bytes = context.get("id_image_bytes")
        selfie_image_bytes = context.get("selfie_image_bytes")
        demo_identity = context.get("demo_identity")

        # 1. Name Match
        name_sim = self._name_similarity(reg_name, extracted_name)
        
        # 2. DOB Match
        dob_match = bool(reg_dob and extracted_dob and (reg_dob == extracted_dob or reg_dob in extracted_dob or extracted_dob in reg_dob))

        reasons = []
        if name_sim >= 0.85:
            reasons.append(f"Name matches registration record ({int(name_sim*100)}% similarity).")
        else:
            reasons.append(f"Name discrepancy detected: registered as '{reg_name}', extracted as '{extracted_name}' ({int(name_sim*100)}% similarity).")

        if reg_dob and extracted_dob:
            if dob_match:
                reasons.append(f"Date of birth ({extracted_dob}) matches registration record.")
            else:
                reasons.append(f"DOB mismatch: registered as '{reg_dob}', extracted as '{extracted_dob}'.")

        # 3. Face Comparison
        if demo_identity:
            # Deterministic demo override
            face_result_status = demo_identity.get("match_status", "MATCH")
            face_sim = demo_identity.get("face_similarity", 0.94)
            face_confidence = 0.94
            id_face_count = 1
            selfie_face_count = 1
            reasons.extend(demo_identity.get("reasons", []))
            if face_result_status == "MATCH":
                reasons.append(f"Face similarity is high ({int(face_sim * 100)}% confidence match).")
            elif face_result_status == "NO_MATCH":
                reasons.append(f"Face comparison indicates mismatch ({int(face_sim * 100)}% similarity).")
            else:
                reasons.append(f"Face comparison inconclusive ({int(face_sim * 100)}% similarity).")
        elif id_image_bytes and selfie_image_bytes:
            face_res = self.face_provider.compare_faces(id_image_bytes, selfie_image_bytes)
            face_result_status = face_res.match_status
            face_sim = face_res.similarity_score
            face_confidence = face_res.confidence
            id_face_count = face_res.id_face_count
            selfie_face_count = face_res.selfie_face_count
            reasons.extend(face_res.reasons)
        else:
            face_result_status = "INCONCLUSIVE"
            face_sim = 0.0
            face_confidence = 0.0
            id_face_count = 0
            selfie_face_count = 0
            reasons.append("Selfie or ID photo missing for facial embedding comparison.")

        # Synthesize identity decision
        if face_result_status == "NO_MATCH" or name_sim < 0.60:
            decision = Decision.REVIEW
            severity = Severity.HIGH
            reasons.append("Identity verification requires organizer review.")
            overall_status = AgentStatus.SUCCESS
        elif face_result_status == "INCONCLUSIVE" or (reg_dob and not dob_match):
            decision = Decision.REVIEW
            severity = Severity.MEDIUM
            overall_status = AgentStatus.INCONCLUSIVE
            reasons.append("Identity matching inconclusive; manual verification suggested.")
        else:
            decision = Decision.PASS
            severity = Severity.LOW
            overall_status = AgentStatus.SUCCESS
            reasons.append("Identity matching passed successfully.")

        confidence = round((name_sim * 0.3) + (face_sim * 0.7), 2)
        confidence = max(0.40, min(0.99, confidence))

        return AgentResult(
            agent=self.name,
            status=overall_status,
            decision=decision,
            confidence=confidence,
            severity=severity,
            reasons=reasons,
            signals={
                "match_status": face_result_status,
                "face_similarity": face_sim,
                "name_similarity": name_sim,
                "dob_match": dob_match,
                "id_face_count": id_face_count,
                "selfie_face_count": selfie_face_count
            }
        )
