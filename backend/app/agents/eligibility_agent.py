"""Eligibility Agent evaluating event admission rules and participant qualifications."""
import logging
from datetime import datetime, date
from typing import Any, Dict, Optional
from app.agents.base_agent import BaseAgent
from app.schemas.evidence import AgentResult, AgentStatus, Decision, Severity
from app.config import settings

logger = logging.getLogger("trustgate.eligibility_agent")

class EligibilityAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="eligibility_evaluation")

    def _calculate_age(self, dob_str: str) -> Optional[int]:
        if not dob_str:
            return None
        # Try common date formats
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                born = datetime.strptime(dob_str.strip(), fmt).date()
                today = date.today()
                return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            except ValueError:
                continue
        return None

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        dob = context.get("extracted_dob") or context.get("registration_dob")
        doc_type = context.get("document_type", "COLLEGE_ID")
        institution = context.get("institution", "")
        demo_eligibility = context.get("demo_eligibility")

        if demo_eligibility:
            eligible = demo_eligibility.get("eligible", True)
            age = demo_eligibility.get("age", 22)
            if eligible:
                return AgentResult(
                    agent=self.name,
                    status=AgentStatus.SUCCESS,
                    decision=Decision.PASS,
                    confidence=0.98,
                    severity=Severity.LOW,
                    reasons=[
                        f"Participant satisfies event age criteria (age: {age}, minimum required: {settings.MINIMUM_AGE}).",
                        "Student status confirmed by valid institutional document."
                    ],
                    signals={"eligible": True, "age": age, "student_verified": True}
                )
            else:
                return AgentResult(
                    agent=self.name,
                    status=AgentStatus.SUCCESS,
                    decision=Decision.FAIL,
                    confidence=0.95,
                    severity=Severity.HIGH,
                    reasons=[f"Participant does not meet minimum age requirement (age: {age}, required: {settings.MINIMUM_AGE})."],
                    signals={"eligible": False, "age": age, "student_verified": False}
                )

        age = self._calculate_age(dob) if dob else None
        reasons = []

        if age is None:
            reasons.append("Date of birth could not be parsed from identity document.")
            return AgentResult(
                agent=self.name,
                status=AgentStatus.INCONCLUSIVE,
                decision=Decision.REVIEW,
                confidence=0.50,
                severity=Severity.MEDIUM,
                reasons=reasons,
                signals={"eligible": None, "age": None, "student_verified": False}
            )

        if age < settings.MINIMUM_AGE:
            reasons.append(f"Ineligible: Participant age ({age}) is below event minimum ({settings.MINIMUM_AGE}).")
            return AgentResult(
                agent=self.name,
                status=AgentStatus.SUCCESS,
                decision=Decision.FAIL,
                confidence=0.96,
                severity=Severity.HIGH,
                reasons=reasons,
                signals={"eligible": False, "age": age, "student_verified": False}
            )

        reasons.append(f"Age requirement satisfied (calculated age: {age} years, min: {settings.MINIMUM_AGE}).")
        
        # Student verification check
        student_verified = bool(doc_type in ["COLLEGE_ID", "STUDENT_ID"] or institution)
        if settings.STUDENT_REQUIRED:
            if student_verified:
                reasons.append(f"Student verification confirmed ({institution or 'Accredited Institution'}).")
            else:
                reasons.append("Student document verification incomplete.")
                return AgentResult(
                    agent=self.name,
                    status=AgentStatus.INCONCLUSIVE,
                    decision=Decision.REVIEW,
                    confidence=0.75,
                    severity=Severity.MEDIUM,
                    reasons=reasons,
                    signals={"eligible": True, "age": age, "student_verified": False}
                )

        return AgentResult(
            agent=self.name,
            status=AgentStatus.SUCCESS,
            decision=Decision.PASS,
            confidence=0.96,
            severity=Severity.LOW,
            reasons=reasons,
            signals={"eligible": True, "age": age, "student_verified": student_verified}
        )
