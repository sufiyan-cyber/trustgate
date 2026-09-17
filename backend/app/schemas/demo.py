"""Pydantic schemas for deterministic demo execution."""
from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.evidence import AgentResult, Decision

class DemoScenarioEnum(str, Enum):
    SCENARIO_A = "A"  # Genuine participant (PASS, Gate opens)
    SCENARIO_B = "B"  # Reused ID (REVIEW, Gate locked)
    SCENARIO_C = "C"  # Tampered ID (REVIEW, Gate locked)
    SCENARIO_D = "D"  # Ambiguous / low quality (REVIEW, Gate locked)
    SCENARIO_E = "E"  # Face mismatch (REVIEW, Gate locked)
    SCENARIO_F = "F"  # Liveness failure (REVIEW, Gate locked)

class DemoRunRequest(BaseModel):
    scenario: DemoScenarioEnum = Field(default=DemoScenarioEnum.SCENARIO_A)
    device_id: str = Field(default="TG-001")
    actuate_hardware: bool = Field(default=True, description="Send physical/simulated command to ESP32 servo")

class DemoRunResponse(BaseModel):
    scenario: str
    scenario_title: str
    scenario_description: str
    is_demo: bool = True
    session_id: str
    decision: Decision
    confidence: float
    risk_level: str
    reasons: List[str]
    gate_action: str
    agent_results: List[AgentResult]
