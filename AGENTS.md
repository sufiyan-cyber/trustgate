# Agents

Framework-agnostic operational instructions and multi-agent architecture reference for the Trust Gate verification system.

## System Overview

Trust Gate operates as a coordinated multi-agent verification pipeline that validates physical identity documents, facial biometrics, and physiological pulse liveness before actuating a physical turnstile gate.

## Sub-Agent Roster

### 1. Extraction Specialist (`extraction-specialist`)
- **Responsibility**: Performs multimodal OCR on identity documents, validates Verhoeff D5 mathematical checksums on Aadhaar numbers, verifies RTO state codes on driving licenses, and masks sensitive PII.
- **Duty Classification**: Assigned to the originating evidence role (`Maker` / `analyst`).
- **Allowed Tools**: `extract-document-ocr`, `validate-verhoeff-checksum`.

### 2. Biometric Verifier (`biometric-verifier`)
- **Responsibility**: Computes 256-dimensional facial embeddings to compare ID card portraits against live webcam selfies, and analyzes MAX30102 infrared photoplethysmography signals for human pulse liveness.
- **Duty Classification**: Assigned to the originating biometric role (`Maker` / `analyst`).
- **Allowed Tools**: `compare-face-embeddings`, `verify-pulse-liveness`.

### 3. Compliance Reviewer (`compliance-reviewer`)
- **Responsibility**: Performs SHA-256 duplicate hash lookups across historical registrations, synthesizes all agent evidence under deterministic safety policies, and authorizes or denies physical gate actuation.
- **Duty Classification**: Assigned to the independent verification role (`Checker` / `reviewer`).
- **Allowed Tools**: `check-duplicate-hash`, `actuate-physical-gate`.

### 4. Gate Auditor (`gate-auditor`)
- **Responsibility**: Verifies post-session compliance, ensures zero plaintext storage of government ID numbers, and records structured audit logs for regulatory inspection.
- **Duty Classification**: Assigned to the oversight role (`Auditor` / `auditor`).
- **Allowed Tools**: `check-duplicate-hash`.

## Execution Order and Safety Interlocks

1. When a participant initiates a session, `extraction-specialist` and `biometric-verifier` collect and score primary evidence.
2. Once primary evidence is assembled, `compliance-reviewer` evaluates duplicate hashes, eligibility constraints, and confidence thresholds.
3. If all checks pass with high confidence, `compliance-reviewer` invokes `actuate-physical-gate` to open the servo turnstile to 90 degrees.
4. If any check fails or falls below the confidence threshold, the gate remains locked at 0 degrees and the session is flagged for human review.
5. Finally, `gate-auditor` records the immutable audit entry.
