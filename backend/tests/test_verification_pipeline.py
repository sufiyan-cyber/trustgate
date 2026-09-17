"""Automated integration tests for Trust Gate verification pipeline and demo scenarios."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "servo_state" in data

def test_dashboard_stats():
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "hardware_status" in data
    assert "recent_sessions" in data

def test_demo_scenarios_list():
    response = client.get("/api/demo/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) == 6
    keys = [s["key"] for s in scenarios]
    assert keys == ["A", "B", "C", "D", "E", "F"]

def test_demo_scenario_a_genuine():
    """Scenario A: Genuine participant -> PASS -> gate action OPEN_GATE"""
    response = client.post("/api/demo/run-scenario", json={
        "scenario": "A",
        "actuate_hardware": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "PASS"
    assert data["gate_action"] == "OPEN_GATE"
    assert data["confidence"] >= 0.90
    assert data["risk_level"] == "LOW"
    assert len(data["reasons"]) > 0

def test_demo_scenario_b_reused_id():
    """Scenario B: Reused ID with different name -> REVIEW -> KEEP_LOCKED"""
    response = client.post("/api/demo/run-scenario", json={
        "scenario": "B",
        "actuate_hardware": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "REVIEW"
    assert data["gate_action"] == "KEEP_LOCKED"
    assert data["risk_level"] == "HIGH"

def test_demo_scenario_c_tampered_id():
    """Scenario C: Tampered ID -> REVIEW -> KEEP_LOCKED"""
    response = client.post("/api/demo/run-scenario", json={
        "scenario": "C",
        "actuate_hardware": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "REVIEW"
    assert data["gate_action"] == "KEEP_LOCKED"

def test_demo_scenario_e_face_mismatch():
    """Scenario E: Face mismatch -> REVIEW -> KEEP_LOCKED"""
    response = client.post("/api/demo/run-scenario", json={
        "scenario": "E",
        "actuate_hardware": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "REVIEW"
    assert data["gate_action"] == "KEEP_LOCKED"

def test_admin_review_workflow():
    """Flagged session can be approved by organizer with audit logging"""
    # 1. Run Scenario B to create a flagged session
    demo_res = client.post("/api/demo/run-scenario", json={"scenario": "B", "actuate_hardware": False})
    session_id = demo_res.json()["session_id"]

    # 2. Inspect flagged sessions
    flagged_res = client.get("/api/review/flagged")
    assert flagged_res.status_code == 200
    flagged = flagged_res.json()
    session_ids = [s["session_id"] for s in flagged]
    assert session_id in session_ids

    # 3. Approve session
    approve_res = client.post(f"/api/review/{session_id}/approve", json={
        "reviewer": "test-admin",
        "reason": "Verified original physical student ID card in person"
    })
    assert approve_res.status_code == 200
    assert approve_res.json()["action"] == "APPROVE"

    # 4. Verify session state updated to PASS
    session_check = client.get(f"/api/verification/{session_id}")
    assert session_check.status_code == 200
    assert session_check.json()["decision"] == "PASS"
