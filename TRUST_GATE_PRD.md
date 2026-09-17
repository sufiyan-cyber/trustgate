# TRUST GATE
## AI-Powered Physical Identity & Eligibility Verification Gateway

**Product Type:** AI + Computer Vision + IoT + Identity Verification  
**Primary Users:** Hackathon/competition organizers and participants  
**Target Platform:** Web application + ESP32 verification kiosk  
**Prototype Goal:** A working physical verification gate that takes a participant through identity verification, combines document, face, duplicate-ID and liveness evidence, produces an explainable decision, and physically opens or keeps locked a gate.

---

## 1. Product Vision

Trust Gate transforms registration verification from:

> Upload ID → OCR → DOB check

into:

> Presence detected → participant initiates verification → ID/selfie captured → AI document analysis → identity verification → duplicate detection → liveness verification → eligibility decision → explainable result → physical gate control

The existing AWS Textract DOB extraction capability must be extended rather than discarded. Trust Gate adds identity verification, document forensics, duplicate/reused-ID detection, liveness evidence, explainable confidence, and a physical access-control layer.

---

## 2. Core Product Principle

Trust Gate must not behave like a simplistic "AI says yes/no" system.

Every decision must be based on multiple evidence sources.

```text
                   +--------------------+
                   | Participant        |
                   +---------+----------+
                             |
                      ID + Selfie
                             |
              +--------------+--------------+
              |                             |
      DOCUMENT EVIDENCE               PERSON EVIDENCE
              |                             |
       Textract/OCR                    Face Match
       Forensics                       Pulse Signal
       Tampering                       Liveness
       Consistency
       Duplicate ID
              |                             |
              +--------------+--------------+
                             |
                       Evidence Engine
                             |
                    +--------+--------+
                    |        |        |
                  PASS     REVIEW    FAIL
                    |        |        |
                  OPEN     HUMAN     LOCK
                           REVIEW
```

Ambiguous evidence should result in `REVIEW`, not an aggressive automatic rejection.

---

## 3. Hardware Stack

| Hardware | Function |
|---|---|
| ESP32 | Main physical-device controller |
| 1080p USB Webcam | ID/selfie capture |
| Capacitive Touch Button | Start verification |
| IR Presence Sensor | Detect participant approaching |
| MAX30102 Pulse Oximeter | Physiological liveness signal |
| 2.4" TFT LCD | Device status, progress and decision |
| Servo Motor | Physical gate open/close |

### Hardware architecture decision

The webcam should be connected to the computer running the Trust Gate application, not directly to the ESP32.

The ESP32 should specialize in:

- IR sensor
- Touch sensor
- MAX30102
- TFT LCD
- Servo

The computer/backend should handle:

- Webcam
- AI
- AWS
- Database
- Dashboard

---

## 4. User Roles

### Participant

Can:

- Approach the gate
- Start verification
- Present ID
- Provide selfie
- Complete liveness interaction
- View verification state/result

Cannot:

- Modify verification results
- Override decisions
- Access administrator controls

### Organizer/Admin

Can:

- View registrations
- View verification results
- Inspect evidence
- Review flagged registrations
- Approve/reject manually
- View duplicate-ID relationships
- View system/device status

---

## 5. Primary User Journey

### State 0 — Idle

LCD:

```text
┌─────────────────────┐
│     TRUST GATE      │
│                     │
│   Scan Station      │
│                     │
│   Waiting...        │
└─────────────────────┘
```

IR sensor continuously monitors for presence.

### State 1 — Person Detected

IR sensor detects a person.

ESP32 sends:

```json
{
  "event": "PERSON_DETECTED",
  "device_id": "TG-001"
}
```

LCD:

```text
┌─────────────────────┐
│    PERSON FOUND     │
│                     │
│   Touch to Start    │
│                     │
│      ● READY        │
└─────────────────────┘
```

No verification begins until the touch button is pressed.

### State 2 — Verification Started

Touch button pressed.

ESP32 sends:

```json
{
  "event": "VERIFICATION_STARTED",
  "device_id": "TG-001"
}
```

LCD:

```text
┌─────────────────────┐
│    VERIFICATION     │
│                     │
│    Starting...      │
│                     │
│       01 / 05       │
└─────────────────────┘
```

Backend creates a verification session with:

- verification_session_id
- participant_id
- device_id
- timestamp
- status = IN_PROGRESS

---

## 6. ID Capture

The web application opens the camera interface.

Participant sees:

```text
POSITION YOUR ID
INSIDE THE FRAME
```

Capture an ID image.

Automatically assess:

- Document present
- Image sufficiently clear
- Document approximately centered

If quality is insufficient:

```text
ID IMAGE TOO BLURRY

Please reposition the document.
```

Do not send unusable images into the AI pipeline.

---

## 7. Selfie Capture

After ID capture:

```text
LOOK AT THE CAMERA

Keep your face inside
the frame.
```

Capture participant selfie.

The verification session contains:

- ID image
- Selfie
- Registration data

---

## 8. Liveness

The participant places a finger on the MAX30102.

LCD:

```text
┌─────────────────────┐
│   LIVENESS CHECK    │
│                     │
│ Place finger here   │
│                     │
│ Detecting pulse...  │
└─────────────────────┘
```

ESP32 collects:

- IR signal
- Red signal
- Pulse presence
- BPM estimate
- Signal quality
- Stability over time

Use MAX30102 primarily as a pulse-presence signal. Do not claim that it alone proves a person is genuine.

Example result:

```json
{
  "pulse_detected": true,
  "signal_quality": 0.91,
  "stable_measurement": true,
  "duration_ms": 5000
}
```

Possible result:

```text
LIVENESS = PASS
```

or

```text
LIVENESS = INCONCLUSIVE
```

A single poor sensor reading should not automatically reject a participant.

---

# 9. AI Architecture

The backend must use specialized AI agents/services rather than one unconstrained LLM prompt.

```text
VerificationOrchestrator
        |
        +-- ExtractionAgent
        +-- DocumentForensicsAgent
        +-- IdentityMatchingAgent
        +-- DuplicateDetectionAgent
        +-- LivenessAgent
        +-- EligibilityAgent
        +-- DecisionAgent
```

---

## 10. Agent 1 — Document Extraction Agent

### Input

ID image.

### Responsibilities

Extract:

- Name
- DOB
- ID number
- ID type
- Institution
- Photo region
- Other relevant fields

### Primary technology

Existing AWS Textract pipeline.

### Output

```json
{
  "name": "...",
  "dob": "...",
  "id_number": "...",
  "id_type": "...",
  "institution": "...",
  "extraction_confidence": 0.96
}
```

---

## 11. Agent 2 — Document Forensics Agent

Analyze whether the document appears:

- Tampered
- Edited
- Inconsistent
- Suspicious
- Excessively compressed
- Blurry
- Structurally abnormal

### Image-level checks

- Unexpected edges
- Copy/paste regions
- Text/photo inconsistencies
- Local compression differences
- Suspicious editing around DOB/name/ID fields

### Semantic consistency

Example:

```text
OCR says:
DOB = 14/05/2005

Visual field appears:
14/05/2008
```

Example output:

```json
{
  "tampering_risk": 0.81,
  "quality_score": 0.93,
  "field_consistency": 0.67,
  "anomalies": [
    "Potential inconsistency near DOB field"
  ]
}
```

---

## 12. Agent 3 — Identity Matching Agent

Inputs:

- Registration name
- ID-extracted name
- Registration DOB
- ID DOB
- ID photo
- Selfie

### Name similarity

Use normalized string matching + fuzzy matching.

### Face matching

Generate face embeddings and compare ID photo vs selfie.

Example:

```json
{
  "face_match_score": 0.94,
  "face_detected_id": true,
  "face_detected_selfie": true
}
```

Agent result:

- MATCH
- NO_MATCH
- INCONCLUSIVE

---

## 13. Agent 4 — Duplicate / Reuse Agent

Search existing registrations using:

- Normalized ID number
- ID type
- Document fingerprint
- Name
- Face embedding

Example:

```text
Current:
ID: KA123456
Name: Rahul

Existing:
ID: KA123456
Name: Sufiyan
```

Output:

```json
{
  "duplicate_detected": true,
  "severity": "HIGH",
  "previous_registrations": 1,
  "conflict_type": "ID_REUSED_WITH_DIFFERENT_NAME"
}
```

---

## 14. Agent 5 — Eligibility Agent

Event rules must be configurable.

Example:

```json
{
  "event_id": "hackathon-2026",
  "minimum_age": 18,
  "student_required": true,
  "accepted_document_types": [
    "COLLEGE_ID",
    "GOVERNMENT_ID"
  ]
}
```

Evaluate:

- DOB
- Age
- Student status
- Institution
- ID type
- Required fields

Example output:

```json
{
  "eligible": true,
  "reason": "Participant satisfies minimum age and student verification requirements."
}
```

---

## 15. Agent 6 — Evidence / Decision Agent

Inputs:

- Document extraction
- Document forensics
- Identity match
- Face match
- Duplicate detection
- Liveness
- Eligibility

Outputs:

- Decision
- Confidence
- Evidence
- Human-readable explanation
- Risk level

---

# 16. Decision Model

Use exactly three outcomes:

## PASS

High-confidence legitimate participant.

## REVIEW

Evidence is conflicting or insufficient.

## FAIL

Strong evidence of invalid eligibility or identity.

Do not make the entire system a single rule such as `score > 70 = PASS`.

Use evidence gates + confidence + severity.

---

# 17. Example Final Result

```json
{
  "decision": "PASS",
  "confidence": 0.96,
  "risk_level": "LOW",
  "reasons": [
    "ID fields successfully extracted",
    "DOB satisfies event age requirement",
    "Name matches registration",
    "Face similarity is high",
    "Pulse signal detected",
    "No previous registration found for this ID",
    "No significant document tampering indicators detected"
  ]
}
```

Human-facing result:

```text
VERIFICATION PASSED

Confidence: 96%

✓ Identity matched
✓ Eligibility confirmed
✓ Document integrity passed
✓ ID not previously used
✓ Liveness signal detected

ACCESS GRANTED
```

---

# 18. Review Result

Example:

```text
VERIFICATION REQUIRES REVIEW

Confidence: 71%

✓ Age requirement satisfied
✓ Face similarity acceptable

⚠ ID previously used
⚠ Name mismatch detected
⚠ Document anomaly detected

Automatic rejection avoided because
the evidence is inconclusive.
```

---

# 19. Physical Gate Logic

The servo must never directly obey an AI agent.

Architecture:

```text
AI agents
    ↓
Decision service
    ↓
APPROVED / REVIEW / REJECTED
    ↓
Hardware policy
    ↓
ESP32
    ↓
Servo
```

### APPROVED

```text
Servo → OPEN
wait 5 seconds
Servo → CLOSE
```

LCD:

```text
✓ VERIFIED

ACCESS GRANTED

Gate closing...
```

### REVIEW

Servo remains closed.

LCD:

```text
⚠ REVIEW REQUIRED

Please contact organizer.
```

### REJECT

Servo remains closed.

LCD:

```text
✕ VERIFICATION FAILED

Access denied.
```

---

# 20. Hardware Communication Protocol

Use structured JSON messages over USB Serial or Wi-Fi.

Suggested events:

```text
DEVICE_READY
PERSON_DETECTED
VERIFY_START
LIVENESS_START
LIVENESS_RESULT
VERIFICATION_PENDING
ACCESS_GRANTED
ACCESS_DENIED
GATE_CLOSE
RESET
```

Example:

```json
{
  "device_id": "TG-001",
  "event": "LIVENESS_RESULT",
  "pulse_detected": true,
  "signal_quality": 0.91
}
```

---

# 21. ESP32 Responsibilities

ESP32 handles only hardware/device state.

### Inputs

- IR sensor
- Touch sensor
- MAX30102

### Outputs

- TFT LCD
- Servo

### Communication

- USB Serial and/or Wi-Fi

### ESP32 should not

- Run LLMs
- Run document forensics
- Perform heavy face recognition
- Store participant databases
- Decide eligibility

---

# 22. Web Application

Build a polished operator dashboard.

### Dashboard home

```text
TRUST GATE

Device Status
● ONLINE

Current Session
#TG-000182

Verification
IN PROGRESS
```

### Live hardware status

```text
IR Sensor       ● READY
Touch Sensor    ● READY
MAX30102        ● READY
LCD             ● ONLINE
Servo           ● LOCKED
Camera          ● ONLINE
```

---

# 23. Verification Screen

Show a multi-stage progress interface:

```text
1  Capture ID          ✓
2  Extract identity    ✓
3  Document forensics  ✓
4  Face match          ✓
5  Liveness            ✓
6  Duplicate check     ✓
7  Eligibility         ✓
8  Decision            ...
```

---

# 24. Evidence Panel

Every verification should expose its evidence.

```text
DOCUMENT
──────────────
Type             College ID
OCR Confidence   96%
Quality          93%

FORENSICS
──────────────
Tampering Risk   8%
Anomalies        None

IDENTITY
──────────────
Name Match       97%
Face Match       94%

LIVENESS
──────────────
Pulse Detected   YES
Signal Quality  91%

DUPLICATE
──────────────
Existing ID      NO

ELIGIBILITY
──────────────
Age              PASS
Student         PASS
```

---

# 25. Admin Review Screen

For every REVIEW result:

```text
VERIFICATION REVIEW

Participant: Rahul XXXXX

────────────────────

DECISION: REVIEW

Reason:
Potential duplicate identity

Evidence:

Current ID
KA123456

Previously Seen
KA123456

Previous Name
Sufiyan XXXXX

Face similarity
78%

Document tampering
Low confidence

────────────────────

[ APPROVE ]   [ REJECT ]
```

Every manual action must be logged.

---

# 26. Database Model

### participants

```text
id
name
email
phone
institution
created_at
```

### registrations

```text
id
participant_id
event_id
status
created_at
```

### identity_documents

```text
id
registration_id
document_type
document_number_hash
name
dob
institution
image_path
created_at
```

Prefer hashed identifiers for duplicate detection rather than storing raw ID numbers unnecessarily.

### verification_sessions

```text
id
registration_id
device_id
status
decision
confidence
started_at
completed_at
```

### verification_evidence

```text
id
session_id
agent_name
result
confidence
reason
raw_output
created_at
```

### liveness_measurements

```text
id
session_id
pulse_detected
signal_quality
bpm
duration
created_at
```

### review_actions

```text
id
session_id
reviewer
action
reason
timestamp
```

---

# 27. Event Configuration

Do not hardcode event rules.

Example:

```json
{
  "event_name": "Hackingly AI Build Challenge",
  "age_rule": {
    "enabled": true,
    "minimum_age": 18
  },
  "student_rule": {
    "enabled": true
  },
  "identity_rule": {
    "face_match_required": true,
    "liveness_required": true
  }
}
```

The product should support different Hackingly events without rewriting core logic.

---

# 28. API Design

Minimum APIs:

```text
POST /api/verification/start
POST /api/verification/{id}/document
POST /api/verification/{id}/selfie
POST /api/verification/{id}/liveness
POST /api/verification/{id}/run
GET  /api/verification/{id}
GET  /api/verification/{id}/evidence

GET  /api/dashboard/stats
GET  /api/registrations
GET  /api/registrations/{id}

POST /api/review/{id}/approve
POST /api/review/{id}/reject

POST /api/device/events
GET  /api/device/{id}/status
POST /api/device/{id}/command
```

---

# 29. Device API

Example:

```http
POST /api/device/TG-001/command
```

```json
{
  "command": "OPEN_GATE",
  "duration_ms": 5000
}
```

ESP32 acknowledgement:

```json
{
  "device_id": "TG-001",
  "event": "GATE_OPENED"
}
```

---

# 30. Failure Handling

### Camera disconnected

```text
CAMERA UNAVAILABLE
```

Do not produce a verification decision.

### MAX30102 unavailable

```text
LIVENESS SENSOR ERROR
```

Do not automatically reject.

### AWS Textract unavailable

```text
DOCUMENT EXTRACTION UNAVAILABLE

Please retry.
```

### AI agent timeout

Retry once, then:

```text
VERIFICATION INCOMPLETE

Manual review required.
```

### ESP32 disconnected

Dashboard:

```text
DEVICE OFFLINE
```

No physical access should be granted.

---

# 31. Security Requirements

### Authentication

Admin dashboard requires authentication.

### Encryption

Use HTTPS/TLS for network communications.

### Sensitive data

ID images and biometric information must not be publicly accessible.

### Logging

Log:

- who
- what
- when
- decision
- reason
- device

### Data minimization

Avoid storing raw biometric information longer than necessary for the prototype.

### No silent overrides

Every manual approval/rejection must create an audit record.

---

# 32. AI Safety / Decision Rule

The AI explanation must never invent evidence.

Bad:

> "The ID is definitely fake because the font looks wrong."

unless the forensic system actually generated that evidence.

Good:

> "The document-forensics model detected a localized image inconsistency near the DOB field with moderate confidence."

Generate explanations only from structured agent outputs.

---

# 33. AI Agent Output Contract

Every agent should return a consistent structure:

```json
{
  "agent": "document_forensics",
  "status": "SUCCESS",
  "decision": "PASS",
  "confidence": 0.94,
  "severity": "LOW",
  "reasons": [
    "No significant localized editing anomalies detected"
  ],
  "signals": {
    "image_quality": 0.96,
    "tampering_probability": 0.08
  }
}
```

Possible statuses:

```text
SUCCESS
INCONCLUSIVE
ERROR
```

Possible decisions:

```text
PASS
REVIEW
FAIL
```

---

# 34. Agent Orchestrator

Use a central orchestrator:

```text
VerificationOrchestrator

        ├── ExtractionAgent
        ├── ForensicsAgent
        ├── IdentityAgent
        ├── DuplicateAgent
        ├── LivenessAgent
        ├── EligibilityAgent
        └── DecisionAgent
```

The orchestrator owns the workflow.

Agents should not call each other randomly.

---

# 35. Recommended Technology Stack

### Frontend

- Next.js
- TypeScript
- Tailwind
- shadcn/ui
- Browser webcam APIs
- Dashboard charts
- Responsive UI

### Backend

- Python
- FastAPI

### Database

- PostgreSQL

### AI / Computer Vision

Use modular adapters so models can be swapped.

Potential components:

- AWS Textract
- Vision model
- Face embedding model
- LLM
- OpenCV

### Hardware bridge

- Python
- PySerial

### ESP32

- Arduino framework and/or ESP-IDF

### Deployment

Prototype:

```text
Laptop
 ├── Next.js
 ├── FastAPI
 ├── PostgreSQL
 └── ESP32 USB

AWS
 ├── Textract
 └── S3
```

---

# 36. Mandatory Demo Mode

The application must include:

```text
DEMO MODE
```

Deterministic demo scenarios:

- Genuine Participant
- Tampered ID
- Duplicate ID
- Face Mismatch
- Liveness Failure
- Manual Review

The UI must clearly mark simulated data as demo/test data.

---

# 37. Demo Scenarios

## Scenario A — Genuine participant

```text
ID ✓
OCR ✓
Forensics ✓
Face ✓
Liveness ✓
Duplicate ✓
Eligibility ✓

CONFIDENCE: 96%

ACCESS GRANTED
```

Servo opens.

## Scenario B — Reused ID

```text
ID ✓
OCR ✓
Forensics ✓
Face ⚠
Duplicate ✕

ID previously registered
under another identity.

REVIEW REQUIRED
```

Gate remains locked.

## Scenario C — Tampered ID

```text
OCR ✓
Document Forensics ✕

Possible modification
detected around DOB field.

REVIEW REQUIRED
```

Gate remains locked.

## Scenario D — Real person, ambiguous evidence

```text
Liveness ✓
Face ✓
Eligibility ✓
Document quality ⚠
Forensics ⚠

CONFIDENCE: 68%

REVIEW REQUIRED

Automatic rejection avoided.
```

---

# 38. Physical Demo Sequence

1. Person walks toward device.
2. IR detects presence.
3. LCD shows `WELCOME — Touch to Verify`.
4. Participant touches button.
5. Webcam captures ID.
6. AI pipeline runs.
7. Dashboard visualizes agent execution.
8. Participant completes MAX30102 liveness check.
9. Decision appears.
10. If approved, servo opens.
11. Servo closes automatically after the configured interval.

---

# 39. Acceptance Criteria

## Hardware

- [ ] IR detects presence
- [ ] Touch button starts verification
- [ ] ESP32 communicates with backend
- [ ] MAX30102 detects pulse signal
- [ ] TFT displays current state
- [ ] Servo opens on approval
- [ ] Servo remains locked on review/rejection

## Identity

- [ ] ID image captured
- [ ] Selfie captured
- [ ] Name extracted
- [ ] DOB extracted
- [ ] ID number extracted
- [ ] ID type identified
- [ ] Face match evaluated
- [ ] Duplicate/reused ID checked

## Forensics

- [ ] Blurry document detected
- [ ] Tampering/anomaly analysis performed
- [ ] Evidence surfaced to user

## Eligibility

- [ ] Event rules configurable
- [ ] Age evaluated
- [ ] Student/identity requirements evaluated

## Decision

- [ ] PASS supported
- [ ] REVIEW supported
- [ ] FAIL supported
- [ ] Confidence generated
- [ ] Human-readable reasoning generated

## Dashboard

- [ ] Live hardware status
- [ ] Verification progress
- [ ] Agent results
- [ ] Evidence panel
- [ ] Registration history
- [ ] Duplicate detection
- [ ] Manual review

---

# 40. Build Priority

## P0 — Absolutely Required

```text
ESP32 ↔ Backend
IR
Touch
LCD
Servo
Webcam
Verification session
Textract
Face match
Duplicate detection
Decision engine
Dashboard
```

## P1 — Strong Demo Features

```text
Document forensics
MAX30102 liveness
Evidence panel
Admin review
Audit logs
Demo mode
```

## P2 — Polish

```text
Beautiful animations
Hardware diagnostics
Advanced analytics
Identity graph visualization
Agent trace visualization
```

---

# 41. Explicit Non-Goals

Do not waste implementation time on:

- Blockchain
- Cryptocurrency
- Unrelated chatbot functionality
- Unnecessary sensors
- Large microservices architecture
- Training a foundation model from scratch
- Making an LLM the final authority
- Generic CRUD screens before the end-to-end verification flow works

---

# 42. Wow Feature — AI Verification Trace

Show the AI agents executing in real time:

```text
┌────────────────────────────────────────┐
│ TRUST GATE AI VERIFICATION TRACE       │
├────────────────────────────────────────┤
│                                        │
│ ✓ Document extracted                  │
│   └─ DOB confidence: 97%              │
│                                        │
│ ✓ Forensics analyzed                  │
│   └─ Tampering risk: 8%               │
│                                        │
│ ✓ Identity compared                   │
│   └─ Face similarity: 94%             │
│                                        │
│ ✓ Duplicate search complete           │
│   └─ No conflict                      │
│                                        │
│ ✓ Liveness verified                   │
│   └─ Pulse detected                   │
│                                        │
│ ✓ Eligibility evaluated               │
│                                        │
│       FINAL DECISION                  │
│          ✓ APPROVED                   │
│                                        │
│        CONFIDENCE 96%                 │
└────────────────────────────────────────┘
```

This gives judges a visible demonstration of the multi-agent architecture instead of merely claiming that agents exist.

---

# 43. Final Product Story

Trust Gate combines:

**Document Intelligence + Identity Intelligence + Physiological Liveness + Physical Access Control**

The system takes an AI verification decision and turns it into a real-world physical access decision.

Core product flow:

```text
Presence
   ↓
Touch
   ↓
ID + Selfie
   ↓
Textract
   ↓
Document Forensics
   ↓
Identity Matching
   ↓
Duplicate Detection
   ↓
MAX30102 Liveness
   ↓
Eligibility
   ↓
Evidence / Decision
   ↓
PASS / REVIEW / FAIL
   ↓
ESP32
   ↓
Servo Gate
```
