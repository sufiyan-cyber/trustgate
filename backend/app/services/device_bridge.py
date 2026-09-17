"""Device Bridge managing physical serial communication, virtual simulation, and state tracking."""
import asyncio
import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable, List, Tuple
import serial
import serial.tools.list_ports
from app.config import settings
from app.services.hardware_policy import HardwarePolicy
from app.database import SessionLocal

logger = logging.getLogger("trustgate.device_bridge")

class DeviceBridge:
    """
    Bi-directional bridge between the backend orchestrator and the physical ESP32.
    Supports:
    - Auto-detection of ESP32 USB COM ports
    - Background serial reader thread
    - Explicit hardware connection verification
    - Active probe / port scanning
    - Thread-safe command dispatch
    - Event listener callbacks (e.g. WebSocket broadcasting)
    """

    def __init__(self):
        self.device_id = settings.DEVICE_ID
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        self.running = False
        self.reader_thread: Optional[threading.Thread] = None
        self.event_listeners: List[Callable[[Dict[str, Any]], None]] = []

        # Current Device State Telemetry
        self.state: Dict[str, Any] = {
            "device_id": self.device_id,
            "online": False,
            "hardware_connected": False,
            "connected_port": None,
            "available_ports": [],
            "ir_presence": False,
            "touch_pressed": False,
            "max30102_ready": False,
            "servo_state": "LOCKED",
            "lcd_state": "WAITING",
            "camera_online": True,
            "last_heartbeat": None,
            "current_session_id": None,
            "processed_command_ids": set()
        }

    def register_listener(self, listener: Callable[[Dict[str, Any]], None]):
        """Registers a callback to receive incoming device events."""
        self.event_listeners.append(listener)

    def notify_listeners(self, event_data: Dict[str, Any]):
        """Notifies all registered listeners of a device event."""
        for listener in self.event_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    asyncio.create_task(listener(event_data))
                else:
                    listener(event_data)
            except Exception as e:
                logger.debug("Error notifying device bridge listener: %s", e)

    def start(self):
        """Starts background hardware connection monitoring."""
        self.running = True
        self.reader_thread = threading.Thread(target=self._connection_loop, daemon=True)
        self.reader_thread.start()
        logger.info("Device bridge started for device: %s", self.device_id)

    def stop(self):
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.is_connected = False
        self.state["online"] = False
        self.state["hardware_connected"] = False
        self.state["connected_port"] = None

    def scan_ports(self) -> List[Dict[str, str]]:
        """Scans and returns all available USB COM ports on the host system."""
        ports = serial.tools.list_ports.comports()
        detected = []
        port_names = []
        for p in ports:
            port_names.append(p.device)
            detected.append({
                "port": p.device,
                "description": p.description or "Unknown",
                "hwid": p.hwid or ""
            })
        self.state["available_ports"] = port_names
        return detected

    def _find_esp32_port(self) -> Optional[str]:
        """Auto-detects ESP32 CP210x, CH340, or FTDI USB serial port."""
        if settings.SERIAL_PORT != "AUTO":
            return settings.SERIAL_PORT

        ports = serial.tools.list_ports.comports()
        port_names = []
        target_port = None
        for p in ports:
            port_names.append(p.device)
            desc = (p.description or "").lower()
            hwid = (p.hwid or "").lower()
            if any(k in desc or k in hwid for k in ["cp210", "ch340", "ch9102", "ftdi", "usb serial", "esp32", "silicon labs"]):
                logger.info("Detected ESP32 device candidate on port: %s (%s)", p.device, p.description)
                target_port = p.device

        self.state["available_ports"] = port_names
        return target_port

    def probe_hardware(self) -> Dict[str, Any]:
        """Actively scans USB COM ports and verifies hardware handshake."""
        available = self.scan_ports()
        target = self._find_esp32_port()

        if target:
            if not self.is_connected or not self.serial_conn or not self.serial_conn.is_open:
                try:
                    logger.info("Probing ESP32 on port %s...", target)
                    self.serial_conn = serial.Serial(
                        target,
                        baudrate=settings.SERIAL_BAUD_RATE,
                        timeout=1.0
                    )
                    self.is_connected = True
                    self.state["online"] = True
                    self.state["hardware_connected"] = True
                    self.state["connected_port"] = target
                    # Send ping
                    self.send_command({"command": "PING"})
                    message = f"Physical ESP32 detected and connected on port {target}."
                except Exception as e:
                    self.is_connected = False
                    self.state["hardware_connected"] = False
                    self.state["connected_port"] = None
                    message = f"Found port {target} but connection failed: {str(e)}"
            else:
                message = f"Physical ESP32 already actively connected on port {self.state['connected_port']}."
        else:
            self.is_connected = False
            self.state["hardware_connected"] = False
            self.state["connected_port"] = None
            if available:
                port_list = ", ".join([p["port"] for p in available])
                message = f"No ESP32 detected. Detected general ports: [{port_list}]. Connect ESP32 USB cable and re-probe."
            else:
                message = "No USB COM serial ports detected on host system. Please connect ESP32 microcontroller."

        status_payload = self.get_status()
        self.notify_listeners({
            "type": "DEVICE_EVENT",
            "device_id": self.device_id,
            "event": "PROBE_RESULT",
            "data": {
                "hardware_connected": self.state["hardware_connected"],
                "connected_port": self.state["connected_port"],
                "available_ports": self.state["available_ports"],
                "message": message
            },
            "state": status_payload
        })

        return {
            "device_id": self.device_id,
            "hardware_connected": self.state["hardware_connected"],
            "connected_port": self.state["connected_port"],
            "available_ports": self.state["available_ports"],
            "detected_devices": available,
            "message": message,
            "status": status_payload
        }

    def _connection_loop(self):
        """Background thread attempting connection and parsing serial messages."""
        while self.running:
            if not self.is_connected:
                port = self._find_esp32_port()
                if port:
                    try:
                        logger.info("Opening serial port %s at %d baud...", port, settings.SERIAL_BAUD_RATE)
                        self.serial_conn = serial.Serial(
                            port,
                            baudrate=settings.SERIAL_BAUD_RATE,
                            timeout=1.0
                        )
                        self.is_connected = True
                        self.state["online"] = True
                        self.state["hardware_connected"] = True
                        self.state["connected_port"] = port
                        logger.info("ESP32 connected successfully on %s", port)
                        self.notify_listeners({
                            "type": "DEVICE_CONNECTED",
                            "device_id": self.device_id,
                            "port": port
                        })
                    except Exception as e:
                        self.is_connected = False
                        self.state["hardware_connected"] = False
                        self.state["connected_port"] = None
                        time.sleep(3.0)
                        continue
                else:
                    # Physical hardware is not connected
                    self.is_connected = False
                    self.state["hardware_connected"] = False
                    self.state["connected_port"] = None
                    # We keep online: True for backend virtual API availability, but hardware_connected: False
                    self.state["online"] = True
                    time.sleep(3.0)
                    continue

            # Read from serial
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    line = self.serial_conn.readline().decode("utf-8", errors="replace").strip()
                    if line:
                        self._handle_serial_line(line)
                else:
                    time.sleep(0.5)
            except Exception as e:
                logger.warning("Serial read error: %s. Disconnecting...", e)
                self.is_connected = False
                self.state["hardware_connected"] = False
                self.state["connected_port"] = None
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except Exception:
                        pass
                time.sleep(3.0)

    def _handle_serial_line(self, line: str):
        """Parses incoming JSON event from ESP32."""
        logger.debug("ESP32 RAW: %s", line)
        try:
            msg = json.loads(line)
            event = msg.get("event")
            if not event:
                return

            self.state["last_heartbeat"] = datetime.now(timezone.utc)
            self.state["hardware_connected"] = True

            if event == "DEVICE_READY":
                logger.info("ESP32 DEVICE_READY received: %s", msg)
                self.state["lcd_state"] = "WAITING"
            elif event == "PERSON_DETECTED":
                self.state["ir_presence"] = True
                self.state["lcd_state"] = "TOUCH_TO_START"
            elif event == "VERIFICATION_STARTED":
                self.state["touch_pressed"] = True
                self.state["lcd_state"] = "SCANNING"
            elif event == "GATE_OPENED":
                self.state["servo_state"] = "OPEN"
                self.state["lcd_state"] = "ACCESS_GRANTED"
            elif event == "GATE_CLOSED":
                self.state["servo_state"] = "LOCKED"
                self.state["lcd_state"] = "WAITING"
            elif event == "HEARTBEAT":
                sensors = msg.get("sensors", {})
                self.state["ir_presence"] = sensors.get("ir", False)
                self.state["touch_pressed"] = sensors.get("touch", False)
                self.state["max30102_ready"] = sensors.get("max30102", True)

            # Broadcast to web dashboard
            self.notify_listeners({
                "type": "DEVICE_EVENT",
                "device_id": self.device_id,
                "event": event,
                "data": msg,
                "state": self.get_status()
            })

        except json.JSONDecodeError:
            logger.debug("Non-JSON line from ESP32: %s", line)

    def send_command(self, cmd_dict: Dict[str, Any]) -> bool:
        """Sends a JSON command line to the physical ESP32 or updates virtual state."""
        payload = json.dumps(cmd_dict) + "\n"
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(payload.encode("utf-8"))
                self.serial_conn.flush()
                logger.info("Dispatched command to physical ESP32: %s", cmd_dict.get("command"))
                return True
            except Exception as e:
                logger.error("Failed to write command to serial: %s", e)
                return False
        else:
            # Virtual execution for simulator / demo
            logger.info("[VIRTUAL] Dispatched simulated command: %s", cmd_dict)
            self._handle_virtual_command(cmd_dict)
            return True

    def _handle_virtual_command(self, cmd: Dict[str, Any]):
        """Simulates device reaction when physical ESP32 is absent."""
        command = cmd.get("command")
        if command == "OPEN_GATE":
            self.state["servo_state"] = "OPEN"
            self.state["lcd_state"] = "ACCESS_GRANTED"
            self.notify_listeners({
                "type": "DEVICE_EVENT",
                "device_id": self.device_id,
                "event": "GATE_OPENED",
                "data": {"command_id": cmd.get("command_id")},
                "state": self.get_status()
            })

            # Auto-lock after duration
            duration_ms = cmd.get("duration_ms", 5000)
            def auto_close():
                time.sleep(duration_ms / 1000.0)
                self.state["servo_state"] = "LOCKED"
                self.state["lcd_state"] = "WAITING"
                self.notify_listeners({
                    "type": "DEVICE_EVENT",
                    "device_id": self.device_id,
                    "event": "GATE_CLOSED",
                    "data": {},
                    "state": self.get_status()
                })
            threading.Thread(target=auto_close, daemon=True).start()

        elif command == "SET_LCD":
            self.state["lcd_state"] = cmd.get("screen", "WAITING")
            self.notify_listeners({
                "type": "DEVICE_EVENT",
                "device_id": self.device_id,
                "event": "LCD_UPDATED",
                "data": cmd,
                "state": self.get_status()
            })
        elif command == "LOCK_GATE":
            self.state["servo_state"] = "LOCKED"
            self.state["lcd_state"] = "WAITING"
            self.notify_listeners({
                "type": "DEVICE_EVENT",
                "device_id": self.device_id,
                "event": "GATE_CLOSED",
                "data": {},
                "state": self.get_status()
            })

    def request_gate_open(self, session_id: str) -> Tuple[bool, str]:
        """
        Executes hardware policy validation before commanding the gate to open.
        Guarantees session authorization and unique command_id.
        """
        db = SessionLocal()
        try:
            is_auth, command_id, reason = HardwarePolicy.authorize_gate_open(
                session_id=session_id,
                device_id=self.device_id,
                is_device_online=self.state["online"],
                db=db
            )
            if not is_auth or not command_id:
                return False, reason

            # Prevent duplicate command execution
            if command_id in self.state["processed_command_ids"]:
                return False, "REPLAY_REJECTED: Stale command ID."

            self.state["processed_command_ids"].add(command_id)

            # Send authoritative command
            cmd = {
                "command": "OPEN_GATE",
                "command_id": command_id,
                "session_id": session_id,
                "duration_ms": settings.GATE_OPEN_DURATION_MS
            }
            success = self.send_command(cmd)
            return success, reason
        finally:
            db.close()

    def set_lcd_state(self, screen: str, message: str = ""):
        """Commands the LCD display to show specific screen."""
        self.state["lcd_state"] = screen
        cmd = {
            "command": "SET_LCD",
            "screen": screen,
            "message": message
        }
        self.send_command(cmd)

    def trigger_virtual_event(self, event_name: str, payload: Dict[str, Any] = None):
        """Allows dashboard / test suite to inject hardware triggers."""
        payload = payload or {}
        if event_name == "PERSON_DETECTED":
            self.state["ir_presence"] = payload.get("detected", True)
            self.state["lcd_state"] = "TOUCH_TO_START"
        elif event_name == "TOUCH_PRESSED":
            self.state["touch_pressed"] = True
            self.state["lcd_state"] = "SCANNING"
        elif event_name == "RESET":
            self.state["ir_presence"] = False
            self.state["touch_pressed"] = False
            self.state["servo_state"] = "LOCKED"
            self.state["lcd_state"] = "WAITING"

        self.notify_listeners({
            "type": "DEVICE_EVENT",
            "device_id": self.device_id,
            "event": event_name,
            "data": payload,
            "state": self.get_status()
        })

    def get_status(self) -> Dict[str, Any]:
        """Returns current hardware status dictionary."""
        return {
            "device_id": self.device_id,
            "online": self.state["online"],
            "hardware_connected": self.state["hardware_connected"],
            "connected_port": self.state["connected_port"],
            "available_ports": self.state["available_ports"],
            "ir_presence": self.state["ir_presence"],
            "touch_pressed": self.state["touch_pressed"],
            "max30102_ready": self.state["max30102_ready"],
            "servo_state": self.state["servo_state"],
            "lcd_state": self.state["lcd_state"],
            "camera_online": self.state["camera_online"],
            "last_heartbeat": self.state["last_heartbeat"].isoformat() if self.state["last_heartbeat"] else None,
            "current_session_id": self.state["current_session_id"]
        }

# Global singleton
device_bridge = DeviceBridge()
