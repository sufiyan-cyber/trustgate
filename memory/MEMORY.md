# Memory

- Default physical gate servo position is `0` degrees (`KEEP_LOCKED`).
- Physical gate actuation (`90` degrees) is strictly restricted to verified `PASS` sessions where all 6 primary agents succeed.
- Plaintext government ID numbers are never persisted; only SHA-256 digests (`document_number_hash`) are stored in the database.
