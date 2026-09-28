"""Document Extraction Agent utilizing Gemini Vision / AWS Textract pipeline with mathematical checksum and government ID validation."""
import logging
import re
from typing import Any, Dict
from app.agents.base_agent import BaseAgent
from app.schemas.evidence import AgentResult, AgentStatus, Decision, Severity
from app.adapters.textract_provider import get_textract_provider
from app.core.security import hash_id_number
from app.core.id_validator import GovernmentIdValidator

logger = logging.getLogger("trustgate.extraction_agent")

class ExtractionAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="document_extraction")
        self.provider = get_textract_provider()

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        id_image_bytes = context.get("id_image_bytes")
        if not id_image_bytes:
            return AgentResult(
                agent=self.name,
                status=AgentStatus.ERROR,
                decision=Decision.REVIEW,
                confidence=0.0,
                severity=Severity.HIGH,
                reasons=["No ID image data provided for extraction."],
                signals={"error": "missing_image_bytes"}
            )

        try:
            data = self.provider.extract_document(id_image_bytes)
            
            # Format hash for sensitive ID number
            id_hash = hash_id_number(data.id_number) if data.id_number else ""

            reasons = []
            if data.provider_source == "GEMINI_VISION":
                reasons.append(f"Document fields extracted via Google Gemini Vision OCR ({int(data.confidence * 100)}% conf).")
            elif data.provider_source == "AWS_TEXTRACT":
                reasons.append(f"Document fields extracted via AWS Textract ({int(data.confidence * 100)}% conf).")
            else:
                reasons.append(f"[DEV OCR] Document fields extracted via local OCR pipeline.")

            if data.name:
                reasons.append(f"Extracted name: '{data.name}'")
            if data.dob:
                reasons.append(f"Extracted DOB: '{data.dob}'")
            if data.id_number:
                clean_digits = re.sub(r"\D", "", data.id_number)
                if len(clean_digits) == 12:
                    masked_id = f"XXXX-XXXX-{clean_digits[-4:]}"
                elif len(data.id_number) > 6:
                    masked_id = data.id_number[:2] + "****" + data.id_number[-4:]
                else:
                    masked_id = data.id_number
                reasons.append(f"Extracted ID: '{masked_id}'")

            # Government Format & Mathematical Checksum Verification
            gov_validation = GovernmentIdValidator.validate_credential(data.id_number, data.id_type)
            reasons.append(gov_validation["reason"])

            # Check completeness & authenticity
            has_essentials = bool(data.name and (data.dob or data.id_number))
            checksum_valid = gov_validation["is_valid"]

            if not checksum_valid:
                decision = Decision.REVIEW
                severity = Severity.HIGH
            elif not has_essentials:
                decision = Decision.REVIEW
                severity = Severity.MEDIUM
            else:
                decision = Decision.PASS
                severity = Severity.LOW

            return AgentResult(
                agent=self.name,
                status=AgentStatus.SUCCESS,
                decision=decision,
                confidence=data.confidence if checksum_valid else min(data.confidence, 0.50),
                severity=severity,
                reasons=reasons,
                signals={
                    "name": data.name,
                    "dob": data.dob,
                    "id_number": data.id_number,
                    "id_number_hash": id_hash,
                    "id_type": gov_validation.get("detected_type", data.id_type),
                    "institution": data.institution,
                    "provider_source": data.provider_source,
                    "checksum_passed": gov_validation["checksum_passed"],
                    "raw_lines": data.raw_lines[:5]
                }
            )

        except Exception as e:
            logger.error("Extraction agent error: %s", e)
            return AgentResult(
                agent=self.name,
                status=AgentStatus.ERROR,
                decision=Decision.REVIEW,
                confidence=0.0,
                severity=Severity.HIGH,
                reasons=[f"Document extraction failed: {str(e)}. Please retry or seek manual review."],
                signals={"exception": str(e)}
            )
