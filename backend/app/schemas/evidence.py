"""Pydantic schemas for AI agent results and verification evidence."""
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class AgentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    INCONCLUSIVE = "INCONCLUSIVE"
    ERROR = "ERROR"

class Decision(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AgentResult(BaseModel):
    """Unified, structured contract returned by every Trust Gate AI agent."""
    agent: str = Field(description="Name of the agent (e.g. document_forensics)")
    status: AgentStatus = Field(description="Execution status (SUCCESS, INCONCLUSIVE, ERROR)")
    decision: Decision = Field(description="Outcome verdict (PASS, REVIEW, FAIL)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    severity: Severity = Field(default=Severity.LOW, description="Severity of detected issues")
    reasons: List[str] = Field(default_factory=list, description="List of factual reasons supporting the decision")
    signals: Dict[str, Any] = Field(default_factory=dict, description="Structured signals, scores, and metrics")

class EvidenceResponse(BaseModel):
    id: str
    session_id: str
    agent_name: str
    status: AgentStatus
    decision: Decision
    confidence: float
    severity: Severity
    reason: Optional[str]
    raw_output: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
