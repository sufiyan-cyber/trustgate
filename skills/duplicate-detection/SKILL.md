---
name: duplicate-detection
description: Performs zero-plaintext SHA-256 cryptographic hash lookups across historical verification records to detect pass-back fraud and credential reuse across different identities.
license: MIT
allowed-tools: check-duplicate-hash
metadata:
  category: fraud-prevention
  globs: backend/app/agents/duplicate_agent.py,backend/app/core/security.py
---

# Duplicate & Reused Credential Detection

## Instructions

1. Normalize the extracted credential identifier by stripping non-alphanumeric characters and converting to uppercase.
2. Compute the one-way 64-character SHA-256 digest (`id_number_hash`) so plaintext ID numbers are never queried or stored.
3. Invoke `check-duplicate-hash` to query the indexed `identity_documents.document_number_hash` column.
4. If a matching hash is bound to a different participant name (`ID_REUSED_WITH_DIFFERENT_NAME`), return `REVIEW` with `HIGH` severity to prevent credential sharing.
5. If no prior registration conflict exists or the hash matches the same participant's repeat check-in, return `PASS`.
