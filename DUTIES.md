# Duties

System-wide segregation of duties policy and role boundaries for the Trust Gate cyber-physical verification system.

## Segregation Principles

No single sub-agent is permitted to extract evidence, approve an identity conflict, and audit its own verification decision. Responsibilities are strictly partitioned across independent operational roles with isolated state and credentials.

## Role Definitions

### Maker Role
- **Assigned Agents**: `extraction-specialist`, `biometric-verifier`
- **Permissions**: `create`, `submit`
- **Scope**: Captures document OCR fields, computes Verhoeff checksums, evaluates facial embedding cosine similarity, and records MAX30102 physiological pulse telemetry into candidate evidence records.
- **Restriction**: This role cannot approve final gate overrides or audit completed verification sessions.

### Checker Role
- **Assigned Agents**: `compliance-reviewer`
- **Permissions**: `review`, `approve`, `reject`
- **Scope**: Independently evaluates the multi-agent evidence dossier, verifies SHA-256 duplicate hash checks, enforces deterministic safety interlocks, and issues the final gate authorization or escalates to human supervision.
- **Restriction**: This role cannot fabricate or modify raw sensor telemetry or OCR extraction outputs.

### Auditor Role
- **Assigned Agents**: `gate-auditor`
- **Permissions**: `audit`, `report`
- **Scope**: Inspects completed verification sessions, verifies that all Aadhaar and government identifiers are masked and SHA-256 hashed, and writes immutable compliance audit logs.
- **Restriction**: This role cannot initiate verification sessions or actuate the physical turnstile servo.

## Conflict Separation Rules

The following role pairs are mutually exclusive and may never be assigned to the same agent:

1. **Originating Evidence vs. Approval Review**:
   - The agent that extracts identity or biometric evidence (`analyst` / originating role) must never approve its own verification dossier (`reviewer` / approval role).
2. **Originating Evidence vs. Compliance Audit**:
   - The agent that generates candidate verification data (`analyst` / originating role) must never audit its own session records (`auditor` role).
3. **Approval Review vs. Compliance Audit**:
   - The agent that approves or rejects gate actuation (`reviewer` / approval role) must never audit its own compliance trail (`auditor` role).

## Mandatory Handoff Workflow

Every physical gate actuation decision (`physical_gate_actuation`) must pass sequentially through independent roles:
1. **Evidence Collection Stage**: Executed by `extraction-specialist` and `biometric-verifier`.
2. **Independent Verification Stage**: Reviewed and authorized by `compliance-reviewer`.
3. **Post-Session Audit Stage**: Logged and verified by `gate-auditor`.
