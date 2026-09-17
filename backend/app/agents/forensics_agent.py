"""Document Forensics Agent for tampering detection, image quality, and anomaly inspection."""
import logging
import cv2
import numpy as np
from typing import Any, Dict, List
from app.agents.base_agent import BaseAgent
from app.schemas.evidence import AgentResult, AgentStatus, Decision, Severity
from app.core.image_utils import load_image_from_bytes, assess_image_quality
from app.config import settings

logger = logging.getLogger("trustgate.forensics_agent")

class DocumentForensicsAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="document_forensics")

    def _error_level_analysis(self, img_bgr: np.ndarray) -> float:
        """
        Calculates localized compression variance using Error Level Analysis (ELA).
        Re-compresses image at 90% JPEG quality and measures difference with original.
        High difference variance indicates potential digital splicing or localized editing.
        """
        try:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            _, encimg = cv2.imencode('.jpg', img_bgr, encode_param)
            recompressed = cv2.imdecode(encimg, 1)

            diff = cv2.absdiff(img_bgr, recompressed)
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            
            # Scale difference
            diff_scaled = cv2.normalize(diff_gray, None, 0, 255, cv2.NORM_MINMAX)
            ela_variance = float(np.var(diff_scaled))
            
            # Map variance to tampering risk (normal unmodified camera images have uniform low ELA variance)
            risk = min(1.0, ela_variance / 400.0)
            return round(risk, 2)
        except Exception:
            return 0.10

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        id_image_bytes = context.get("id_image_bytes")
        extracted_data = context.get("extracted_data", {})
        demo_forensics = context.get("demo_forensics") or context.get("demo_anomaly")

        # Handle demo simulation mode
        if demo_forensics:
            risk = demo_forensics.get("tampering_risk", 0.05)
            q_score = demo_forensics.get("quality_score", 0.95)
            anomalies = demo_forensics.get("anomalies", [])
            field_cons = demo_forensics.get("field_consistency", 0.98)
            reasons = []

            if risk >= 0.70 or len(anomalies) >= 2:
                dec = Decision.REVIEW
                sev = Severity.HIGH
                reasons.append(f"Potential document tampering detected (tampering risk: {int(risk*100)}%).")
                for a in anomalies:
                    reasons.append(f"Anomaly: {a}")
                reasons.append("Forensic flags require manual inspection before granting physical access.")
            elif risk >= 0.30 or len(anomalies) > 0:
                dec = Decision.REVIEW
                sev = Severity.MEDIUM
                reasons.append("Moderate image anomalies detected; routing to review to avoid false rejection.")
                for a in anomalies:
                    reasons.append(f"Anomaly: {a}")
            else:
                dec = Decision.PASS
                sev = Severity.LOW
                reasons.append("No significant localized editing or structural tampering indicators detected.")
                reasons.append("Document image quality and consistency verified.")

            return AgentResult(
                agent=self.name,
                status=AgentStatus.SUCCESS,
                decision=dec,
                confidence=round(q_score * (1.0 - (risk * 0.2)), 2),
                severity=sev,
                reasons=reasons,
                signals={
                    "tampering_risk": risk,
                    "quality_score": q_score,
                    "field_consistency": field_cons,
                    "anomalies": anomalies,
                    "is_blurry": False
                }
            )

        if not id_image_bytes:
            return AgentResult(
                agent=self.name,
                status=AgentStatus.ERROR,
                decision=Decision.REVIEW,
                confidence=0.0,
                severity=Severity.HIGH,
                reasons=["No document image provided for forensic analysis."],
                signals={"error": "missing_image"}
            )

        img = load_image_from_bytes(id_image_bytes)
        if img is None:
            return AgentResult(
                agent=self.name,
                status=AgentStatus.ERROR,
                decision=Decision.REVIEW,
                confidence=0.0,
                severity=Severity.HIGH,
                reasons=["Document image could not be decoded."],
                signals={"error": "decode_failed"}
            )

        # 1. Quality & Blur Assessment
        quality_score, quality_signals = assess_image_quality(id_image_bytes)
        is_blurry = quality_signals.get("is_blurry", False)

        # 2. Tampering & Compression (ELA)
        ela_risk = self._error_level_analysis(img)

        # 3. Anomaly detection
        anomalies: List[str] = []
        reasons: List[str] = []

        if is_blurry:
            anomalies.append(f"Image sharpness ({quality_signals['sharpness_var']}) is below clear document threshold (65.0).")
            reasons.append("Document image exhibits noticeable blur.")

        if ela_risk > settings.TAMPERING_RISK_THRESHOLD:
            anomalies.append("Elevated compression noise variance detected near document text boundaries.")
            reasons.append(f"Potential localized editing detected (tampering risk: {int(ela_risk*100)}%).")

        # In case of demo anomaly injection (e.g. Scenario C)
        if forced_anomaly:
            anomalies.extend(forced_anomaly.get("anomalies", []))
            ela_risk = max(ela_risk, forced_anomaly.get("tampering_risk", 0.82))
            reasons.extend(forced_anomaly.get("reasons", []))

        # Field consistency evaluation
        field_consistency = 0.95
        if anomalies:
            field_consistency = max(0.40, round(0.95 - (0.2 * len(anomalies)), 2))

        # Decision logic
        if ela_risk >= 0.70 or len(anomalies) >= 2:
            decision = Decision.REVIEW
            severity = Severity.HIGH
            reasons.append("Forensic flags require manual inspection before granting physical access.")
        elif ela_risk >= 0.35 or is_blurry:
            decision = Decision.REVIEW
            severity = Severity.MEDIUM
            reasons.append("Moderate image anomalies detected; routing to review to avoid false rejection.")
        else:
            decision = Decision.PASS
            severity = Severity.LOW
            reasons.append("No significant localized editing or structural tampering indicators detected.")

        confidence = round(quality_score * (1.0 - (ela_risk * 0.3)), 2)
        confidence = max(0.50, min(0.98, confidence))

        return AgentResult(
            agent=self.name,
            status=AgentStatus.SUCCESS,
            decision=decision,
            confidence=confidence,
            severity=severity,
            reasons=reasons,
            signals={
                "tampering_risk": ela_risk,
                "quality_score": quality_score,
                "field_consistency": field_consistency,
                "anomalies": anomalies,
                "sharpness_var": quality_signals.get("sharpness_var"),
                "is_blurry": is_blurry
            }
        )
