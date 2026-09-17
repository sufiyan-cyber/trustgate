"""Pydantic schemas for verification sessions and lifecycles."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.evidence import AgentResult, Decision, EvidenceResponse

class VerificationStartRequest(BaseModel):
    registration_id: Optional[str] = None
    device_id: str = Field(default="TG-001")
    is_demo: bool = False

class VerificationStartResponse(BaseModel):
    session_id: str
    registration_id: Optional[str] = None
    device_id: str
    status: str
    started_at: datetime

class LivenessSubmitRequest(BaseModel):
    pulse_detected: bool = Field(description="AC pulsatile signal detected")
    signal_quality: float = Field(ge=0.0, le=1.0, description="Signal-to-noise quality score")
    bpm: Optional[float] = Field(default=None, description="Estimated heart rate (informational only)")
    duration_ms: int = Field(default=5000, description="Measurement duration in milliseconds")
    stable_measurement: bool = Field(default=True, description="Stability over window")
    waveform_quality: Optional[float] = Field(default=0.85, description="Waveform regularity")

class VerificationSessionResponse(BaseModel):
    id: str
    registration_id: Optional[str]
    device_id: str
    status: str
    decision: str
    confidence: float
    risk_level: str
    reasons: List[str]
    is_demo: bool
    started_at: datetime
    completed_at: Optional[datetime]
    evidence: Optional[List[EvidenceResponse]] = None

    class Config:
        from_attributes = True

class VerificationRunResponse(BaseModel):
    session_id: str
    decision: Decision
    confidence: float
    risk_level: str
    reasons: List[str]
    agent_results: List[AgentResult]
    gate_command: str  # OPEN_GATE, KEEP_LOCKED
    completed_at: datetime
