"""Deterministic mock data and demo scenarios for Trust Gate."""
from typing import Dict, Any

DEMO_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "A": {
        "title": "Scenario A — Genuine Participant",
        "description": "High-quality ID, matching selfie, verified age, clean duplicate history, confirmed pulse.",
        "expected_decision": "PASS",
        "expected_confidence": 0.96,
        "risk_level": "LOW",
        "gate_action": "OPEN_GATE",
        "participant": {
            "name": "Sarah Jenkins",
            "email": "sarah.jenkins@university.edu",
            "phone": "+1-555-0199",
            "institution": "Stanford University",
            "dob": "2004-03-15"
        },
        "document": {
            "document_type": "COLLEGE_ID",
            "id_number": "STU-8829104",
            "name": "Sarah Jenkins",
            "dob": "2004-03-15",
            "institution": "Stanford University"
        },
        "liveness": {
            "pulse_detected": True,
            "signal_quality": 0.93,
            "bpm": 74.0,
            "duration_ms": 5000,
            "stable_measurement": True
        },
        "forensics": {
            "tampering_risk": 0.05,
            "quality_score": 0.95,
            "field_consistency": 0.98,
            "anomalies": []
        },
        "identity": {
            "match_status": "MATCH",
            "face_similarity": 0.94,
            "name_similarity": 1.0,
            "dob_match": True
        },
        "duplicate": {
            "duplicate_detected": False,
            "conflict_type": "NONE",
            "previous_registrations": 0
        },
        "eligibility": {
            "eligible": True,
            "age": 22,
            "student_verified": True
        },
        "reasons": [
            "ID fields successfully extracted via AWS Textract",
            "DOB satisfies event age requirement (age: 22)",
            "Name matches registration record exactly",
            "Face similarity is high (94% confidence match)",
            "Pulse signal detected with stable 74 BPM physiological waveform",
            "No previous registration found for this ID",
            "No document tampering or editing indicators detected"
        ]
    },
    "B": {
        "title": "Scenario B — Reused ID with Different Name",
        "description": "ID card number matches a previously registered participant with a completely different identity.",
        "expected_decision": "REVIEW",
        "expected_confidence": 0.65,
        "risk_level": "HIGH",
        "gate_action": "KEEP_LOCKED",
        "participant": {
            "name": "Rahul Verma",
            "email": "rahul.v@tech.ac.in",
            "phone": "+91-9876543210",
            "institution": "National Institute of Technology",
            "dob": "2003-08-20"
        },
        "document": {
            "document_type": "COLLEGE_ID",
            "id_number": "KA123456",  # Reused ID
            "name": "Rahul Verma",
            "dob": "2003-08-20",
            "institution": "National Institute of Technology"
        },
        "liveness": {
            "pulse_detected": True,
            "signal_quality": 0.89,
            "bpm": 78.0,
            "duration_ms": 5000,
            "stable_measurement": True
        },
        "forensics": {
            "tampering_risk": 0.12,
            "quality_score": 0.88,
            "field_consistency": 0.90,
            "anomalies": []
        },
        "identity": {
            "match_status": "MATCH",
            "face_similarity": 0.89,
            "name_similarity": 1.0,
            "dob_match": True
        },
        "duplicate": {
            "duplicate_detected": True,
            "conflict_type": "ID_REUSED_WITH_DIFFERENT_NAME",
            "previous_registrations": 1,
            "previous_participant_name": "Sufiyan Ahmed",
            "previous_registration_date": "2026-09-10"
        },
        "eligibility": {
            "eligible": True,
            "age": 23,
            "student_verified": True
        },
        "reasons": [
            "CRITICAL CONFLICT: ID number KA123456 was previously registered by 'Sufiyan Ahmed'",
            "Current participant name 'Rahul Verma' does not match prior owner",
            "Document integrity and face match appear valid",
            "Gate kept locked; session routed to Admin Review for manual credential inspection"
        ]
    },
    "C": {
        "title": "Scenario C — Tampered Document",
        "description": "Visual field analysis detects localized tampering and compression anomalies around the DOB area.",
        "expected_decision": "REVIEW",
        "expected_confidence": 0.58,
        "risk_level": "HIGH",
        "gate_action": "KEEP_LOCKED",
        "participant": {
            "name": "Alex Mercer",
            "email": "alex.m@domain.org",
            "phone": "+1-555-4921",
            "institution": "Metro College",
            "dob": "2002-11-04"
        },
        "document": {
            "document_type": "GOVERNMENT_ID",
            "id_number": "GOV-9938210",
            "name": "Alex Mercer",
            "dob": "2008-11-04",  # Inconsistent
            "institution": "State Authority"
        },
        "liveness": {
            "pulse_detected": True,
            "signal_quality": 0.91,
            "bpm": 80.0,
            "duration_ms": 5000,
            "stable_measurement": True
        },
        "forensics": {
            "tampering_risk": 0.82,
            "quality_score": 0.74,
            "field_consistency": 0.45,
            "anomalies": [
                "Localized edge discontinuity near Date of Birth bounding box",
                "High Error Level Analysis (ELA) variance around year digits '2008'",
                "Font kerning mismatch compared to document template standard"
            ]
        },
        "identity": {
            "match_status": "MATCH",
            "face_similarity": 0.88,
            "name_similarity": 0.95,
            "dob_match": False
        },
        "duplicate": {
            "duplicate_detected": False,
            "conflict_type": "NONE",
            "previous_registrations": 0
        },
        "eligibility": {
            "eligible": True,
            "age": 22,
            "student_verified": True
        },
        "reasons": [
            "Document Forensics detected localized image tampering near DOB field (tampering risk: 82%)",
            "Semantic discrepancy between visual DOB and registration record",
            "Physical gate remains locked pending organizer document inspection"
        ]
    },
    "D": {
        "title": "Scenario D — Ambiguous Evidence / Degraded Quality",
        "description": "Document is somewhat blurry and lighting is poor; automatic rejection is avoided in favor of manual review.",
        "expected_decision": "REVIEW",
        "expected_confidence": 0.68,
        "risk_level": "MEDIUM",
        "gate_action": "KEEP_LOCKED",
        "participant": {
            "name": "Maria Garcia",
            "email": "maria.g@polytech.edu",
            "phone": "+1-555-8820",
            "institution": "Polytechnic Institute",
            "dob": "2001-05-18"
        },
        "document": {
            "document_type": "COLLEGE_ID",
            "id_number": "POL-449102",
            "name": "Maria Garcia",
            "dob": "2001-05-18",
            "institution": "Polytechnic Institute"
        },
        "liveness": {
            "pulse_detected": True,
            "signal_quality": 0.62,
            "bpm": 88.0,
            "duration_ms": 4200,
            "stable_measurement": False
        },
        "forensics": {
            "tampering_risk": 0.35,
            "quality_score": 0.52,
            "field_consistency": 0.70,
            "anomalies": [
                "Moderate image blur detected (Laplacian variance below optimal threshold)",
                "Glare reflection partially covers institution logo"
            ]
        },
        "identity": {
            "match_status": "INCONCLUSIVE",
            "face_similarity": 0.68,
            "name_similarity": 0.92,
            "dob_match": True
        },
        "duplicate": {
            "duplicate_detected": False,
            "conflict_type": "NONE",
            "previous_registrations": 0
        },
        "eligibility": {
            "eligible": True,
            "age": 25,
            "student_verified": True
        },
        "reasons": [
            "Document image quality degraded by glare and motion blur",
            "Face similarity score (68%) falls in inconclusive zone",
            "Automatic rejection avoided per system policy; routed to human review"
        ]
    },
    "E": {
        "title": "Scenario E — Face Mismatch",
        "description": "Selfie camera captures a face that does not match the photo on the presented identity card.",
        "expected_decision": "REVIEW",
        "expected_confidence": 0.60,
        "risk_level": "HIGH",
        "gate_action": "KEEP_LOCKED",
        "participant": {
            "name": "David Chen",
            "email": "dchen@ivy.edu",
            "phone": "+1-555-3312",
            "institution": "Ivy University",
            "dob": "2003-01-22"
        },
        "document": {
            "document_type": "COLLEGE_ID",
            "id_number": "IVY-009214",
            "name": "David Chen",
            "dob": "2003-01-22",
            "institution": "Ivy University"
        },
        "liveness": {
            "pulse_detected": True,
            "signal_quality": 0.90,
            "bpm": 72.0,
            "duration_ms": 5000,
            "stable_measurement": True
        },
        "forensics": {
            "tampering_risk": 0.08,
            "quality_score": 0.92,
            "field_consistency": 0.95,
            "anomalies": []
        },
        "identity": {
            "match_status": "NO_MATCH",
            "face_similarity": 0.32,  # Low similarity
            "name_similarity": 1.0,
            "dob_match": True
        },
        "duplicate": {
            "duplicate_detected": False,
            "conflict_type": "NONE",
            "previous_registrations": 0
        },
        "eligibility": {
            "eligible": True,
            "age": 23,
            "student_verified": True
        },
        "reasons": [
            "Face similarity (32%) is significantly below matching threshold",
            "Selfie does not match photo on presented college ID",
            "Gate locked; flagged for organizer inspection"
        ]
    },
    "F": {
        "title": "Scenario F — Liveness Failure (No Pulse / Sensor Noise)",
        "description": "Participant failed to hold finger steady on the MAX30102 sensor or withdrew early.",
        "expected_decision": "REVIEW",
        "expected_confidence": 0.71,
        "risk_level": "LOW",
        "gate_action": "KEEP_LOCKED",
        "participant": {
            "name": "Emma Watson",
            "email": "emma.w@oxford.edu",
            "phone": "+44-7700-9001",
            "institution": "Oxford Academy",
            "dob": "2002-04-12"
        },
        "document": {
            "document_type": "COLLEGE_ID",
            "id_number": "OXF-77192",
            "name": "Emma Watson",
            "dob": "2002-04-12",
            "institution": "Oxford Academy"
        },
        "liveness": {
            "pulse_detected": False,
            "signal_quality": 0.22,
            "bpm": None,
            "duration_ms": 1500,  # Withdrew early
            "stable_measurement": False
        },
        "forensics": {
            "tampering_risk": 0.06,
            "quality_score": 0.94,
            "field_consistency": 0.96,
            "anomalies": []
        },
        "identity": {
            "match_status": "MATCH",
            "face_similarity": 0.93,
            "name_similarity": 1.0,
            "dob_match": True
        },
        "duplicate": {
            "duplicate_detected": False,
            "conflict_type": "NONE",
            "previous_registrations": 0
        },
        "eligibility": {
            "eligible": True,
            "age": 24,
            "student_verified": True
        },
        "reasons": [
            "MAX30102 pulse signal interrupted (duration: 1.5s, required: 4.0s)",
            "Liveness sensor inconclusive; not treated as fraud",
            "Gate locked; participant invited to retry or see registration desk"
        ]
    }
}
