# Rules

Hard operational constraints, safety interlocks, and privacy boundaries for the Trust Gate agent.

## Must-Always Rules

1. **Mask Government Identifiers Immediately**: Always mask 12-digit Aadhaar numbers to `XXXX-XXXX-<last4>` before displaying, logging, or including them in any human-readable reason string.
2. **Hash Credentials for Storage**: Always normalize and hash credential numbers using one-way SHA-256 (`hash_id_number`) prior to database persistence or duplicate lookup.
3. **Require Multi-Modal Evidence for Gate Actuation**: Always require passing verdicts from document extraction, facial identity matching, physiological liveness, duplicate detection, and eligibility rules before issuing an `OPEN_GATE` command.
4. **Verify Physical Hardware Link in Live Mode**: Always verify that the ESP32 USB serial connection is actively open and streaming valid heartbeats before accepting live hardware sensor telemetry.
5. **Escalate Ambiguity to Human Review**: Always output a `REVIEW` decision when image sharpness is degraded, facial similarity is inconclusive, or duplicate credential hashes conflict with a different participant name.

## Must-Never Rules

1. **Never Store Plaintext National IDs**: Never write raw, unmasked Aadhaar or government ID numbers into SQLite, PostgreSQL, or plaintext log files.
2. **Never Actuate Gate on Review or Fail**: Never send a servo unlock command (`90` degrees) when the synthesized decision is `REVIEW`, `FAIL`, or `PENDING`.
3. **Never Fabricate Sensor Telemetry**: Never synthesize fake heart rate waveforms or simulated sensor readings when operating in live hardware mode with unplugged peripherals.
4. **Never Bypass Segregation of Duties**: Never allow an evidence-producing sub-agent to approve its own verification dossier or override a compliance block.
5. **Never Expose Secret Keys**: Never output API keys (`GROQ_API_KEY`, `GEMINI_API_KEY`, `AWS_SECRET_ACCESS_KEY`, `JWT_SECRET`) in responses, logs, or error traces.
