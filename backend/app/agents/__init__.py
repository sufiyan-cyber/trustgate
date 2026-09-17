"""Agents package initialization."""
from app.agents.base_agent import BaseAgent
from app.agents.extraction_agent import ExtractionAgent
from app.agents.forensics_agent import DocumentForensicsAgent
from app.agents.identity_agent import IdentityMatchingAgent
from app.agents.duplicate_agent import DuplicateDetectionAgent
from app.agents.liveness_agent import LivenessAgent
from app.agents.eligibility_agent import EligibilityAgent
from app.agents.decision_agent import DecisionAgent

__all__ = [
    "BaseAgent",
    "ExtractionAgent",
    "DocumentForensicsAgent",
    "IdentityMatchingAgent",
    "DuplicateDetectionAgent",
    "LivenessAgent",
    "EligibilityAgent",
    "DecisionAgent",
]
