"""Device API routes for telemetry, events, and authoritative hardware commands."""
import asyncio
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.device import DeviceEventRequest, DeviceCommandRequest, DeviceStatusResponse
from app.services.device_bridge import device_bridge
from app.routers.ws import ws_manager

logger = logging.getLogger("trustgate.device_router")

router = APIRouter(prefix="/api/device", tags=["Hardware Device"])

@router.post("/events")
async def receive_device_event(event_req: DeviceEventRequest):
    """
    Receives hardware event from ESP32 or simulator:
    - PERSON_DETECTED
    - VERIFICATION_STARTED
    - LIVENESS_RESULT
    - GATE_OPENED
    - GATE_CLOSED
    - HEARTBEAT
    """
    event_name = event_req.event
    device_id = event_req.device_id

    logger.info("Received device event '%s' from %s", event_name, device_id)

    # Process through device bridge
    device_bridge.trigger_virtual_event(event_name, event_req.model_dump())

    # Broadcast to dashboard via WebSocket
    await ws_manager.broadcast({
        "type": "DEVICE_EVENT",
        "device_id": device_id,
        "event": event_name,
        "data": event_req.model_dump(),
        "state": device_bridge.get_status()
    })

    return {"status": "ACK", "event": event_name, "device_id": device_id}

@router.get("/{device_id}/status", response_model=DeviceStatusResponse)
async def get_device_status(device_id: str):
    """Returns current hardware status and sensor telemetry."""
    status = device_bridge.get_status()
    return status

@router.post("/{device_id}/probe")
async def probe_device_connection(device_id: str):
    """
    Actively probes USB serial ports on host to verify physical ESP32 connectivity.
    Returns detected ports and connection handshake result.
    """
    result = device_bridge.probe_hardware()
    # Broadcast probe result over websocket
    await ws_manager.broadcast({
        "type": "DEVICE_EVENT",
        "device_id": device_id,
        "event": "PROBE_RESULT",
        "data": result,
        "state": device_bridge.get_status()
    })
    return result

@router.get("/ports")
async def list_available_ports():
    """Lists all detected COM / USB serial ports on host machine."""
    return {"ports": device_bridge.scan_ports()}

@router.post("/{device_id}/command")
async def send_device_command(device_id: str, cmd_req: DeviceCommandRequest, db: Session = Depends(get_db)):
    """
    Dispatches authoritative backend command to ESP32:
    - OPEN_GATE (strictly protected by hardware safety policy)
    - LOCK_GATE
    - SET_LCD
    - START_LIVENESS
    - RESET
    """
    command = cmd_req.command
    logger.info("Authoritative command requested: %s for %s", command, device_id)

    if command == "OPEN_GATE":
        if not cmd_req.session_id:
            raise HTTPException(
                status_code=400,
                detail="Hardware safety violation: session_id is required to open the physical gate."
            )
        authorized, reason = device_bridge.request_gate_open(cmd_req.session_id)
        if not authorized:
            raise HTTPException(status_code=403, detail=f"Gate open rejected by policy: {reason}")
        return {"status": "SUCCESS", "command": command, "message": reason}

    elif command == "LOCK_GATE":
        device_bridge.send_command({"command": "LOCK_GATE"})
        return {"status": "SUCCESS", "command": command}

    elif command == "SET_LCD":
        device_bridge.set_lcd_state(cmd_req.screen or "WAITING", cmd_req.message or "")
        return {"status": "SUCCESS", "command": command, "screen": cmd_req.screen}

    elif command == "RESET":
        device_bridge.trigger_virtual_event("RESET")
        device_bridge.send_command({"command": "RESET"})
        return {"status": "SUCCESS", "command": command}

    else:
        success = device_bridge.send_command(cmd_req.model_dump())
        return {"status": "SUCCESS" if success else "FAILED", "command": command}
