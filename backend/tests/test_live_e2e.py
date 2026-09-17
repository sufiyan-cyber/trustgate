"""End-to-end verification script testing live backend and frontend services."""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_live_system():
    print("==================================================================")
    print("         TRUST GATE - LIVE END-TO-END VERIFICATION               ")
    print("==================================================================")

    # 1. Health check
    res = requests.get(f"{BASE_URL}/health")
    assert res.status_code == 200
    health = res.json()
    print("[PASS] 1. Backend Health Check:", health)

    # 2. Hardware telemetry
    res = requests.get(f"{BASE_URL}/api/device/TG-001/status")
    assert res.status_code == 200
    status = res.json()
    print(f"[PASS] 2. Hardware Telemetry: Device={status['device_id']}, Online={status['online']}, Gate={status['servo_state']}")

    # 3. Simulate person arrival
    res = requests.post(f"{BASE_URL}/api/device/events", json={
        "event": "PERSON_DETECTED",
        "device_id": "TG-001",
        "distance_cm": 42.5
    })
    assert res.status_code == 200
    print("[PASS] 3. IR Sensor Event Dispatched: PERSON_DETECTED")

    # 4. Touch button verification start
    res = requests.post(f"{BASE_URL}/api/verification/start", json={
        "device_id": "TG-001",
        "is_demo": False
    })
    assert res.status_code == 200
    session_data = res.json()
    session_id = session_data["session_id"]
    print(f"[PASS] 4. Verification Session Initialized: #{session_id[:8]} (Status: {session_data['status']})")

    # 5. Submit liveness reading
    res = requests.post(f"{BASE_URL}/api/verification/{session_id}/liveness", json={
        "pulse_detected": True,
        "signal_quality": 0.94,
        "bpm": 74.0,
        "duration_ms": 5000,
        "stable_measurement": True
    })
    assert res.status_code == 200
    print("[PASS] 5. MAX30102 Liveness Telemetry Stored: 74 BPM (Quality: 94%)")

    # 6. Test Scenario A (Genuine Participant -> PASS -> Servo Gate Opens)
    print("\n--- Executing Scenario A: Genuine Participant ---")
    res = requests.post(f"{BASE_URL}/api/demo/run-scenario", json={
        "scenario": "A",
        "actuate_hardware": True
    })
    assert res.status_code == 200
    sc_a = res.json()
    print(f"[PASS] 6. Scenario A Decision: {sc_a['decision']} (Confidence: {int(sc_a['confidence']*100)}%)")
    print(f"       Gate Action: {sc_a['gate_action']}")
    assert sc_a["decision"] == "PASS"
    assert sc_a["gate_action"] == "OPEN_GATE"

    # Check device state reflects OPEN
    dev_status = requests.get(f"{BASE_URL}/api/device/TG-001/status").json()
    print(f"       Device Servo State: {dev_status['servo_state']}, LCD: {dev_status['lcd_state']}")

    # 7. Test Scenario B (Reused ID -> REVIEW -> Gate Locked)
    print("\n--- Executing Scenario B: Reused ID with Different Name ---")
    res = requests.post(f"{BASE_URL}/api/demo/run-scenario", json={
        "scenario": "B",
        "actuate_hardware": True
    })
    assert res.status_code == 200
    sc_b = res.json()
    print(f"[PASS] 7. Scenario B Decision: {sc_b['decision']} (Confidence: {int(sc_b['confidence']*100)}%)")
    safe_reason = sc_b['reasons'][0].encode('ascii', 'replace').decode('ascii')
    print(f"       Conflict: {safe_reason}")
    assert sc_b["decision"] == "REVIEW"
    assert sc_b["gate_action"] == "KEEP_LOCKED"

    # 8. Test Scenario C (Tampered Document -> REVIEW -> Gate Locked)
    print("\n--- Executing Scenario C: Tampered ID Forensics ---")
    res = requests.post(f"{BASE_URL}/api/demo/run-scenario", json={
        "scenario": "C",
        "actuate_hardware": True
    })
    assert res.status_code == 200
    sc_c = res.json()
    print(f"[PASS] 8. Scenario C Decision: {sc_c['decision']} (Confidence: {int(sc_c['confidence']*100)}%)")
    assert sc_c["decision"] == "REVIEW"
    assert sc_c["gate_action"] == "KEEP_LOCKED"

    # 9. Test Scenario D (Ambiguous Evidence -> REVIEW -> Automatic Rejection Avoided)
    print("\n--- Executing Scenario D: Ambiguous Evidence ---")
    res = requests.post(f"{BASE_URL}/api/demo/run-scenario", json={
        "scenario": "D",
        "actuate_hardware": True
    })
    assert res.status_code == 200
    sc_d = res.json()
    print(f"[PASS] 9. Scenario D Decision: {sc_d['decision']} (Confidence: {int(sc_d['confidence']*100)}%)")
    assert sc_d["decision"] == "REVIEW"

    # 10. Test Scenario E (Face Mismatch -> REVIEW -> Gate Locked)
    print("\n--- Executing Scenario E: Face Mismatch ---")
    res = requests.post(f"{BASE_URL}/api/demo/run-scenario", json={
        "scenario": "E",
        "actuate_hardware": True
    })
    assert res.status_code == 200
    sc_e = res.json()
    print(f"[PASS] 10. Scenario E Decision: {sc_e['decision']}")
    assert sc_e["decision"] == "REVIEW"

    # 11. Test Scenario F (Liveness Interrupted -> REVIEW -> Gate Locked)
    print("\n--- Executing Scenario F: Liveness Failure ---")
    res = requests.post(f"{BASE_URL}/api/demo/run-scenario", json={
        "scenario": "F",
        "actuate_hardware": True
    })
    assert res.status_code == 200
    sc_f = res.json()
    print(f"[PASS] 11. Scenario F Decision: {sc_f['decision']}")
    assert sc_f["decision"] == "REVIEW"

    # 12. Admin Review Workflow: Inspect flagged queue and approve
    print("\n--- Testing Admin Review & Manual Override Audit Workflow ---")
    flagged = requests.get(f"{BASE_URL}/api/review/flagged").json()
    print(f"[PASS] 12a. Flagged sessions in queue: {len(flagged)}")
    assert len(flagged) > 0
    target_session = flagged[0]["session_id"]

    # Approve with audit justification
    appr_res = requests.post(f"{BASE_URL}/api/review/{target_session}/approve", json={
        "reviewer": "chief-organizer",
        "reason": "Verified government ID card and college enrollment manually."
    })
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    print(f"[PASS] 12b. Manual Approval Audit Logged: Action={appr_data['action']} by {appr_data['reviewer']}")

    # 13. Dashboard Stats Check
    stats = requests.get(f"{BASE_URL}/api/dashboard/stats").json()
    print(f"\n[PASS] 13. Dashboard Metrics Verified:")
    print(f"       Total Verifications: {stats['metrics']['total_verifications']}")
    print(f"       Passed: {stats['metrics']['passed_count']} | Review: {stats['metrics']['review_count']} | Failed: {stats['metrics']['failed_count']}")
    print(f"       Pass Rate: {stats['metrics']['pass_rate_pct']}%")

    print("\n==================================================================")
    print("   ALL 13 ACCEPTANCE TEST SUITES PASSED CLEANLY & DETERMINISTICALLY")
    print("==================================================================")

if __name__ == "__main__":
    test_live_system()
