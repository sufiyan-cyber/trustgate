"""Base agent definition and interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict
from app.schemas.evidence import AgentResult, AgentStatus, Decision, Severity

class BaseAgent(ABC):
    """Abstract base class for all Trust Gate specialized verification agents."""
    
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> AgentResult:
        """Executes the agent's task and returns a structured AgentResult."""
        pass
