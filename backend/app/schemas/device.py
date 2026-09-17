"""Pydantic schemas for hardware device communication and state."""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

class DeviceEventRequest(BaseModel):
    event: str = Field(description="Event name: PERSON_DETECTED, VERIFICATION_STARTED, LIVENESS_RESULT, GATE_OPENED, GATE_CLOSED, HEARTBEAT")
    device_id: str = Field(default="TG-001")
    distance_cm: Optional[float] = None
    pulse_detected: Optional[bool] = None
    signal_quality: Optional[float] = None
    bpm: Optional[float] = None
    duration_ms: Optional[int] = None
    sensors: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class DeviceCommandRequest(BaseModel):
    command: str = Field(description="Command name: OPEN_GATE, LOCK_GATE, SET_LCD, START_LIVENESS, RESET")
    session_id: Optional[str] = Field(default=None, description="Active session ID for security gating")
    command_id: Optional[str] = Field(default=None, description="Unique command ID to prevent replay")
    duration_ms: Optional[int] = 5000
    screen: Optional[str] = None
    message: Optional[str] = None

class DeviceStatusResponse(BaseModel):
    device_id: str
    online: bool
    hardware_connected: bool = False
    connected_port: Optional[str] = None
    available_ports: List[str] = []
    ir_presence: bool
    touch_pressed: bool
    max30102_ready: bool
    servo_state: str  # LOCKED, OPEN
    lcd_state: str    # WAITING, TOUCH_TO_START, SCANNING, LIVENESS, ACCESS_GRANTED, REVIEW_REQUIRED, VERIFICATION_FAILED
    camera_online: bool
    last_heartbeat: Optional[datetime]
    current_session_id: Optional[str]
