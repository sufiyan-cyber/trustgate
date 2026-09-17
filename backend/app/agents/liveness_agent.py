"""Liveness Agent evaluating MAX30102 physiological pulse signals."""
import logging
from typing import Any, Dict
from app.agents.base_agent import BaseAgent
from app.schemas.evidence import AgentResult, AgentStatus, Decision, Severity
from app.config import settings

logger = logging.getLogger("trustgate.liveness_agent")

class LivenessAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="liveness_verification")

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        liveness_data = context.get("liveness_data", {})
        demo_liveness = context.get("demo_liveness")

        if demo_liveness:
            liveness_data = demo_liveness

        pulse_detected = liveness_data.get("pulse_detected", False)
        signal_quality = liveness_data.get("signal_quality", 0.0)
        bpm = liveness_data.get("bpm")
        duration_ms = liveness_data.get("duration_ms", 0)
        stable_measurement = liveness_data.get("stable_measurement", False)
        waveform_quality = liveness_data.get("waveform_quality", 0.85)

        reasons = []
        signals = {
            "pulse_detected": pulse_detected,
            "signal_quality": signal_quality,
            "bpm": bpm,
            "duration_ms": duration_ms,
            "stable_measurement": stable_measurement,
            "waveform_quality": waveform_quality
        }

        # Check for hardware error or absence of data
        if not liveness_data:
            return AgentResult(
                agent=self.name,
                status=AgentStatus.ERROR,
                decision=Decision.REVIEW,
                confidence=0.0,
                severity=Severity.MEDIUM,
                reasons=["No physiological signal received from MAX30102 sensor."],
                signals={"error": "missing_sensor_reading"}
            )

        # Evaluate liveness quality and stability
        if pulse_detected and signal_quality >= settings.LIVENESS_MIN_QUALITY and duration_ms >= settings.LIVENESS_MIN_DURATION_MS:
            bpm_info = f" with physiological heart rate {int(bpm)} BPM" if bpm else ""
            reasons.append(f"Stable pulsatile blood volume signal detected{bpm_info} (quality: {int(signal_quality*100)}%).")
            reasons.append("MAX30102 physiological liveness verified.")
            return AgentResult(
                agent=self.name,
                status=AgentStatus.SUCCESS,
                decision=Decision.PASS,
                confidence=round(signal_quality, 2),
                severity=Severity.LOW,
                reasons=reasons,
                signals=signals
            )
        elif not pulse_detected or duration_ms < settings.LIVENESS_MIN_DURATION_MS:
            reasons.append(
                f"MAX30102 sensor contact interrupted or incomplete (duration: {duration_ms}ms, required: {settings.LIVENESS_MIN_DURATION_MS}ms)."
            )
            reasons.append("Signal inconclusive; does not prove fraud, but requires manual assistance or retry.")
            return AgentResult(
                agent=self.name,
                status=AgentStatus.INCONCLUSIVE,
                decision=Decision.REVIEW,
                confidence=round(max(0.20, signal_quality), 2),
                severity=Severity.MEDIUM,
                reasons=reasons,
                signals=signals
            )
        else:
            # Low SNR / noisy measurement
            reasons.append(f"Noisy or degraded pulse signal quality ({int(signal_quality*100)}%).")
            reasons.append("Physiological reading inconclusive; automatic rejection avoided per policy.")
            return AgentResult(
                agent=self.name,
                status=AgentStatus.INCONCLUSIVE,
                decision=Decision.REVIEW,
                confidence=round(signal_quality, 2),
                severity=Severity.LOW,
                reasons=reasons,
                signals=signals
            )
