"""Decision Agent synthesizing multi-agent evidence into explainable justifications with Groq + Gemini LLM failover."""
import logging
from typing import Any, Dict, List
from app.agents.base_agent import BaseAgent
from app.schemas.evidence import AgentResult, AgentStatus, Decision, Severity
from app.services.decision_engine import DecisionEngine
from app.adapters.llm_provider import llm_engine

logger = logging.getLogger("trustgate.decision_agent")

class DecisionAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="decision_synthesis")

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        agent_results: List[AgentResult] = context.get("agent_results", [])
        decision, confidence, risk_level, reasons, gate_command = DecisionEngine.evaluate(agent_results)

        severity_map = {
            "LOW": Severity.LOW,
            "MEDIUM": Severity.MEDIUM,
            "HIGH": Severity.HIGH
        }

        # Format clean bullet points derived strictly from structured signals
        formatted_reasons = []
        for r in reasons:
            clean = r.strip()
            if clean and not clean.startswith(("✓", "✕", "⚠")):
                prefix = "✓ " if decision == Decision.PASS else ("⚠ " if decision == Decision.REVIEW else "✕ ")
                formatted_reasons.append(f"{prefix}{clean}")
            else:
                formatted_reasons.append(clean)

        # Build context for LLM explainability
        evidence_summary = []
        for r in agent_results:
            evidence_summary.append(f"- {r.agent}: {r.decision} (conf: {r.confidence:.0%}) -> {'; '.join(r.reasons)}")

        prompt = (
            f"Verification Outcome: {decision.value}\n"
            f"Confidence: {confidence:.0%}\n"
            f"Risk Level: {risk_level}\n"
            f"Upstream Evidence:\n" + "\n".join(evidence_summary) + "\n\n"
            "Provide a concise 1-2 sentence executive briefing for an event security auditor."
        )
        system_prompt = (
            "You are TrustGate's Audit Intelligence Agent. "
            "Summarize evidence with absolute fidelity to the provided signals. "
            "Never contradict the decision or invent outside facts."
        )

        llm_res = llm_engine.generate_explanation(prompt, system_prompt)

        # Include LLM explanation in reasons if available
        if llm_res.provider_used in ["GROQ", "GEMINI"] and llm_res.text:
            formatted_reasons.insert(0, f"AI Auditor Brief ({llm_res.provider_used}): {llm_res.text}")

        return AgentResult(
            agent=self.name,
            status=AgentStatus.SUCCESS,
            decision=decision,
            confidence=confidence,
            severity=severity_map.get(risk_level, Severity.LOW),
            reasons=formatted_reasons,
            signals={
                "risk_level": risk_level,
                "gate_command": gate_command,
                "evaluated_agent_count": len(agent_results),
                "llm_provider": llm_res.provider_used,
                "llm_model": llm_res.model,
                "llm_failover": llm_res.failover_occurred,
            }
        )
