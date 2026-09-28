---
name: document-extraction
description: Extracts structured identity fields from student IDs, Aadhaar cards, and driving licenses using multimodal vision OCR and validates Verhoeff D5 mathematical checksums.
license: MIT
allowed-tools: extract-document-ocr validate-verhoeff-checksum
metadata:
  category: computer-vision
  globs: backend/app/agents/extraction_agent.py,backend/app/core/id_validator.py
---

# Document Extraction & Checksum Verification

## Instructions

1. Ingest the document image frame and evaluate Laplacian edge sharpness to ensure the credential is legible (`sharpness_var >= 65.0`).
2. Invoke `extract-document-ocr` to parse `name`, `dob`, `id_number`, `institution`, and `id_type` (`COLLEGE_ID` or `GOVERNMENT_ID`).
3. Invoke `validate-verhoeff-checksum` on the extracted `id_number`:
   - For 12-digit Aadhaar numbers, verify that the first digit is not `0` or `1`, reject trivial repeating digits, and verify the Verhoeff dihedral group $D_5$ checksum.
   - For Indian Driving Licenses, verify the 2-letter RTO state code and 4-digit issue year.
4. Immediately mask sensitive 12-digit numbers to `XXXX-XXXX-<last4>` and compute the SHA-256 hash (`id_number_hash`).
5. Return `PASS` if essential fields are present and mathematical checksums pass; otherwise return `REVIEW`.
