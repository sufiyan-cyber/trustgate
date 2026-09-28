---
name: liveness-verification
description: Evaluates physiological photoplethysmography (PPG) telemetry from the MAX30102 optical pulse sensor to confirm human vitality and prevent photo or screen spoofing.
license: MIT
allowed-tools: verify-pulse-liveness
metadata:
  category: hardware-telemetry
  globs: backend/app/agents/liveness_agent.py,backend/app/services/device_bridge.py
---

# Physiological Liveness Verification

## Instructions

1. Receive MAX30102 infrared and red photoplethysmography sensor measurements captured over a 4-second fingertip contact window.
2. Invoke `verify-pulse-liveness` to evaluate:
   - Pulsatile AC/DC component presence (`pulse_detected == true`).
   - Signal-to-noise quality score (`signal_quality >= 0.65`).
   - Physiological heart rate bounds (`45.0 <= bpm <= 165.0`).
   - Measurement stability across the sampling window (`stable_measurement == true`).
3. If no pulse is detected, return `FAIL` with high severity to block spoofed entry.
4. If signal quality is noisy or unstable, return `REVIEW` and prompt for sensor re-measurement.
5. If all physiological vitality criteria are satisfied, return `PASS`.
