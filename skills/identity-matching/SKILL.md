---
name: identity-matching
description: Cross-verifies extracted document fields against participant registration records and computes 256-dimensional facial embedding cosine similarity between ID portraits and live selfies.
license: MIT
allowed-tools: compare-face-embeddings
metadata:
  category: biometrics
  globs: backend/app/agents/identity_agent.py,backend/app/adapters/face_provider.py
---

# Identity Matching & Facial Biometrics

## Instructions

1. Normalize both the registered participant name and the OCR-extracted document name, then compute token-subset and Ratcliff-Obershelp sequence similarity.
2. Compare the extracted date of birth against the registration record if present.
3. Invoke `compare-face-embeddings` with the ID card image and the live webcam selfie:
   - Detect frontal faces using Haar cascades and YCrCb skin-locus contour localization.
   - Extract 256-dimensional L2-normalized facial feature vectors and calculate cosine similarity.
4. Combine name similarity ($30\%$ weight) and facial similarity ($70\%$ weight) into a calibrated confidence score.
5. Return `PASS` when facial match status is `MATCH` and name similarity $\ge 0.85$; otherwise return `REVIEW`.
