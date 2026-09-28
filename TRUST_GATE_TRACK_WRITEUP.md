# TRUST GATE — OpenGAP Cyber-Physical Identity & Access Control Domain Worker

**Track**: 01 — Custom Claw Workers (Deployable OpenGAP-Compliant Domain Worker)  
**Agent Name**: `trust-gate` (`spec_version: 0.1.0`)  
**Repository**: https://github.com/sufiyan-cyber/trustgate  
**Author**: Sufiyan (`sufiyan-cyber`)  
**License**: MIT  

---

## 1. Executive Summary

**Trust Gate** is a deployable, OpenGAP-compliant cyber-physical domain worker that bridges multimodal AI identity verification with physical turnstile hardware actuation. Built for high-security campus gateways, hackathons, and regulated facilities, Trust Gate verifies physical identity documents, computes 256-dimensional facial biometric similarity, validates mathematical government ID checksums (Verhoeff dihedral group D5), and measures real-time human arterial pulse liveness via an ESP32 + MAX30102 optical photoplethysmography sensor before unlocking a physical servo gate.

By adopting the **OpenGAP / GitAgent (`v0.1.0`)** specification, Trust Gate separates its identity (`SOUL.md`), hard safety boundaries (`RULES.md`), Segregation of Duties (`DUTIES.md`), decision transparency (`EXPLAINABILITY.md`), reusable capabilities (`skills/`), and MCP-compatible tool schemas (`tools/`) into a version-controlled, framework-agnostic repository that exports cleanly across all **15 supported agent frameworks** (including OpenClaw, Claude Code, OpenAI Agents SDK, CrewAI, Lyzr, Gemini CLI, Cursor, and GitClaw).

---

## 2. The Problem

Physical access control at events, universities, and regulated venues suffers from three critical vulnerabilities:
1. **Manual Inspection Bottlenecks & Forgery**: Security guards visually glancing at ID cards cannot mathematically validate whether a 12-digit Aadhaar number or 15-character Driving License number is structurally genuine or fabricated.
2. **Biometric Spoofing**: Standard webcam check-in kiosks can be fooled by holding up a high-resolution photograph or smartphone video of another person.
3. **Plaintext PII Liability**: Conventional check-in apps store raw government ID numbers in plaintext databases, violating UIDAI guidelines, GDPR, and India's Digital Personal Data Protection (DPDP) Act.

---

## 3. Domain Worker Architecture & Multi-Agent Pipeline

Trust Gate orchestrates four specialized OpenGAP sub-agents governed by strict **Segregation of Duties (Maker / Checker / Auditor)**:

### A. Originating Evidence Role (`Maker` / `analyst`)
1. **Extraction Specialist (`agents/extraction-specialist`)**
   - Uses **Google Gemini 1.5 Flash Multimodal Vision** (with AWS Textract and local OCR fallback) to extract `name`, `dob`, `id_number`, and `institution`.
   - Validates 12-digit Aadhaar numbers using the **Verhoeff Dihedral Group D5 Checksum Algorithm** and verifies Indian Driving Licenses against all 36 authorized RTO state codes.
   - Immediately masks sensitive numbers to `XXXX-XXXX-<last4>` and computes a one-way **SHA-256 hash** (`document_number_hash`).
2. **Biometric Verifier (`agents/biometric-verifier`)**
   - Evaluates document sharpness using the **Laplacian Variance ($\nabla^2 f$)** kernel (rejecting blurry frames below `65.0`).
   - Extracts **256-dimensional L2-normalized facial embeddings** from the ID portrait and live webcam selfie, computing cosine similarity ($\ge 0.75$ threshold).
   - Evaluates 4-second infrared photoplethysmography (PPG) waveforms from the **MAX30102 pulse oximeter** to verify a living human pulse (`45–165 BPM`).

### B. Independent Verification Role (`Checker` / `reviewer`)
3. **Compliance Reviewer (`agents/compliance-reviewer`)**
   - Performs $O(1)$ SHA-256 hash collision lookups against historical registrations (`check-duplicate-hash`) to block pass-back fraud and credential sharing across different names.
   - Synthesizes all agent evidence using **Groq (`llama-3.3-70b-versatile`)** with automatic failover to **Google Gemini (`gemini-1.5-flash`)** under deterministic safety interlocks:
     - **PASS**: All checks succeed with confidence $\ge 0.80$ $\rightarrow$ invokes `actuate-physical-gate` to open the physical servo turnstile to $90^\circ$.
     - **REVIEW**: Blurry capture, inconclusive biometrics, or duplicate ID conflict $\rightarrow$ keeps servo locked at $0^\circ$ and routes the dossier to a human supervisor.
     - **FAIL**: Failed pulse liveness or underage/ineligible registrant $\rightarrow$ keeps servo locked at $0^\circ$ and denies access.

### C. Oversight Role (`Auditor` / `auditor`)
4. **Gate Auditor (`agents/gate-auditor`)**
   - Verifies post-session compliance, ensures zero plaintext storage of government IDs, and writes immutable structured JSON audit logs retained for regulatory inspection.

---

## 4. OpenGAP (`v0.1.0`) Specification & Portability

Trust Gate implements the complete OpenGAP standard in the repository root:

| OpenGAP Artifact | Path | Purpose in Trust Gate |
| :--- | :--- | :--- |
| **Manifest** | `agent.yaml` | Defines `spec_version: "0.1.0"`, model failover, skills, tools, sub-agents, and FINRA / SR 11-7 / GDPR compliance policies. |
| **Identity** | `SOUL.md` | Defines clinical precision, zero-fabrication values, privacy-by-design principles, and behavioral boundaries. |
| **Explainability** | `EXPLAINABILITY.md` | Documents **Decision and Reasoning: How It Decides**, **Input, Data Source, and Data Used**, and **Limitation, Constraint, and Known Issue Analysis**. |
| **Segregation of Duties** | `DUTIES.md` & `AGENTS.md` | Enforces strict separation between `Maker`, `Checker`, and `Auditor` roles across the 4 sub-agents. |
| **Safety Rules** | `RULES.md` | Enforces 5 Must-Always and 5 Must-Never rules (zero plaintext IDs, fail-closed servo interlocks). |
| **Skills (5)** | `skills/*/SKILL.md` | `document-extraction`, `identity-matching`, `liveness-verification`, `duplicate-detection`, `gate-decision-synthesis`. |
| **Tools (6)** | `tools/*.yaml` | `extract-document-ocr`, `validate-verhoeff-checksum`, `compare-face-embeddings`, `verify-pulse-liveness`, `check-duplicate-hash`, `actuate-physical-gate`. |

### Verified Across All 15 Framework Export Adapters
Running `npx @open-gitagent/opengap validate --compliance` passes with **0 errors and 0 warnings**, and `npx @open-gitagent/opengap export -f <format>` succeeds across all 15 target runtimes:
`openclaw`, `gitclaw`, `claude-code`, `openai`, `crewai`, `lyzr`, `gemini`, `cursor`, `copilot`, `opencode`, `nanobot`, `github`, `codex`, `kiro`, and `system-prompt`.

---

## 5. Privacy, Security & Data Governance

1. **Zero Plaintext ID Storage**: The database schema (`identity_documents`) has no plaintext ID column—only `document_number_hash` (SHA-256) is stored.
2. **Real-Time UIDAI Masking**: Aadhaar numbers are masked to `XXXX-XXXX-1234` before logging or UI display.
3. **Non-Invertible Biometrics**: Facial comparisons operate on 256D floating-point embeddings, and raw physiological pulse waveforms are flushed upon session completion.
4. **Live Hardware Heartbeat Verification**: In Live Mode, the backend actively probes host COM ports (`POST /api/device/TG-001/probe`) and refuses to display simulated telemetry when physical sensors are unplugged.

---

## 6. How to Run & Verify

### Validate OpenGAP Compliance & Export to OpenClaw
```bash
npx @open-gitagent/opengap validate --compliance
npx @open-gitagent/opengap export -f openclaw
```

### Run Full-Stack Verification Gateway
```bash
# 1. Start FastAPI Multi-Agent Backend (Port 8000)
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Start Next.js Verification Kiosk & Admin Dashboard (Port 3000)
cd frontend
npm install
npm run dev

# 3. Run End-to-End Automated Pipeline Tests
cd backend
python -m pytest tests/test_live_e2e.py
```
