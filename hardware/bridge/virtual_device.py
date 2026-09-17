"""Virtual ESP32 Hardware Simulator CLI for testing Trust Gate without physical board."""
import json
import time
import requests

BACKEND_URL = "http://localhost:8000"

def simulate_workflow():
    print("==================================================")
    print("      TRUST GATE - VIRTUAL ESP32 SIMULATOR        ")
    print("==================================================")
    print("1. Simulate Person Approach (IR Trigger)")
    print("2. Simulate Touch Button Pressed (Start Verification)")
    print("3. Simulate MAX30102 Pulse Reading (Liveness Result)")
    print("4. Check Device Status on Backend")
    print("5. Reset Virtual Device to Idle")
    print("6. Run Full Autonomous Hardware Loop")
    print("0. Exit")
    print("==================================================")

    while True:
        choice = input("\nEnter choice [0-6]: ").strip()
        if choice == "0":
            break
        elif choice == "1":
            res = requests.post(f"{BACKEND_URL}/api/device/events", json={
                "event": "PERSON_DETECTED",
                "device_id": "TG-001",
                "distance_cm": 45.0
            })
            print("Response:", res.json())
        elif choice == "2":
            res = requests.post(f"{BACKEND_URL}/api/device/events", json={
                "event": "VERIFICATION_STARTED",
                "device_id": "TG-001"
            })
            print("Response:", res.json())
        elif choice == "3":
            res = requests.post(f"{BACKEND_URL}/api/device/events", json={
                "event": "LIVENESS_RESULT",
                "device_id": "TG-001",
                "pulse_detected": True,
                "signal_quality": 0.93,
                "bpm": 74.0,
                "duration_ms": 5000
            })
            print("Response:", res.json())
        elif choice == "4":
            res = requests.get(f"{BACKEND_URL}/api/device/TG-001/status")
            print("Device Status:", json.dumps(res.json(), indent=2))
        elif choice == "5":
            res = requests.post(f"{BACKEND_URL}/api/device/TG-001/command", json={
                "command": "RESET"
            })
            print("Reset Response:", res.json())
        elif choice == "6":
            print("\n[AUTO-RUN] 1. Person approaches...")
            requests.post(f"{BACKEND_URL}/api/device/events", json={"event": "PERSON_DETECTED", "device_id": "TG-001"})
            time.sleep(1.5)
            print("[AUTO-RUN] 2. Touch button pressed...")
            requests.post(f"{BACKEND_URL}/api/device/events", json={"event": "VERIFICATION_STARTED", "device_id": "TG-001"})
            time.sleep(1.5)
            print("[AUTO-RUN] 3. Finger placed on MAX30102...")
            requests.post(f"{BACKEND_URL}/api/device/events", json={
                "event": "LIVENESS_RESULT",
                "device_id": "TG-001",
                "pulse_detected": True,
                "signal_quality": 0.94,
                "bpm": 72.0,
                "duration_ms": 5000
            })
            print("[AUTO-RUN] Hardware sequence complete. Check Dashboard!")

if __name__ == "__main__":
    simulate_workflow()
