---
name: gate-decision-synthesis
description: Synthesizes multi-agent evidence using Groq and Gemini dual-LLM reasoning with deterministic safety interlocks to govern physical servo turnstile actuation.
license: MIT
allowed-tools: actuate-physical-gate
metadata:
  category: decision-orchestration
  globs: backend/app/agents/decision_agent.py,backend/app/services/decision_engine.py
---

# Gate Decision Synthesis & Hardware Actuation

## Instructions

1. Aggregate structured `AgentResult` records from document extraction, forensics, identity matching, liveness verification, duplicate detection, and eligibility rules.
2. Apply deterministic safety guardrails first:
   - Any `FAIL` verdict from liveness or eligibility immediately forces a `FAIL` outcome and `KEEP_LOCKED` gate command.
   - Any `REVIEW` verdict or overall confidence below $0.80$ forces a `REVIEW` outcome and `KEEP_LOCKED` gate command.
3. Synthesize a concise, factual explanation of the decision using Groq (`llama-3.3-70b-versatile`) with automatic failover to Google Gemini (`gemini-1.5-flash`).
4. Only when the synthesized verdict is `PASS`, invoke `actuate-physical-gate` to rotate the physical servo turnstile to $90^\circ$ and display `ACCESS_GRANTED` on the 2.4-inch TFT LCD.
