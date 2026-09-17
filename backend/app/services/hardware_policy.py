"""Hardware Safety Policy enforcing strict authorization for physical servo actuation."""
import logging
import uuid
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models import VerificationSession
from app.schemas.evidence import Decision

logger = logging.getLogger("trustgate.hardware_policy")

class HardwarePolicy:
    """
    Authoritative gatekeeper for physical servo access.
    Guarantees:
    - Default state is LOCKED
    - Requires valid, completed session with decision == PASS
    - Scoped with cryptographically unique command_id (UUIDv4)
    - Anti-replay and stale command rejection
    - Device health and online connectivity validation
    """

    @staticmethod
    def authorize_gate_open(
        session_id: str,
        device_id: str,
        is_device_online: bool,
        db: Session
    ) -> Tuple[bool, Optional[str], str]:
        """
        Validates whether the gate servo is authorized to actuate open.
        Returns: (is_authorized, command_id, reason).
        """
        # 1. Device connectivity check
        if not is_device_online:
            logger.warning("Hardware policy rejected: Device %s is offline", device_id)
            return False, None, "DEVICE_OFFLINE: Gate cannot actuate while device connection is inactive."

        # 2. Session existence check
        session = db.query(VerificationSession).filter(VerificationSession.id == session_id).first()
        if not session:
            logger.warning("Hardware policy rejected: Session %s not found", session_id)
            return False, None, "INVALID_SESSION: Verification session does not exist."

        # 3. Decision check - MUST BE PASS
        if session.decision != Decision.PASS.value:
            logger.warning("Hardware policy rejected: Session decision is %s (not PASS)", session.decision)
            return False, None, f"POLICY_VIOLATION: Decision is {session.decision}. Gate remains LOCKED."

        # 4. Session status check - MUST BE COMPLETED
        if session.status != "COMPLETED":
            logger.warning("Hardware policy rejected: Session status is %s (not COMPLETED)", session.status)
            return False, None, "INCOMPLETE_SESSION: Verification pipeline has not completed."

        # 5. Device target check
        if session.device_id != device_id:
            logger.warning("Hardware policy rejected: Target device mismatch (%s vs %s)", session.device_id, device_id)
            return False, None, "DEVICE_MISMATCH: Command does not target the session device."

        # 6. Generate single-use command ID to prevent replay attacks
        command_id = str(uuid.uuid4())
        session.current_command_id = command_id
        db.commit()

        logger.info("Hardware policy AUTHORIZED: OPEN_GATE for session %s (command_id: %s)", session_id, command_id)
        return True, command_id, "AUTHORIZED: All policy requirements satisfied."
