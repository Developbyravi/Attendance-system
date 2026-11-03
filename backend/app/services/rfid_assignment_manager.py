import time
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone

class RfidAssignmentSession:
    def __init__(
        self,
        session_id: str,
        student_id: int,
        student_name: str,
        roll_no: str,
        department: str,
        division: str,
        admin_id: str,
        current_rfid_uid: Optional[str] = None,
        device_id: Optional[str] = "GATE-READER-01",
        mode: str = "ASSIGN",
        timeout_seconds: int = 60
    ):
        now = time.time()
        self.session_id = session_id
        self.student_id = student_id
        self.student_name = student_name
        self.roll_no = roll_no
        self.department = department
        self.division = division
        self.admin_id = admin_id
        self.current_rfid_uid = current_rfid_uid
        self.device_id = device_id
        self.mode = mode
        self.status = "PENDING_SCAN" # "PENDING_SCAN" | "SCANNED" | "CONFIRMED" | "CANCELLED" | "EXPIRED"
        self.scanned_uid: Optional[str] = None
        self.created_at = now
        self.expires_at = now + timeout_seconds
        self.error: Optional[str] = None

    def is_expired(self) -> bool:
        if self.status == "PENDING_SCAN" and time.time() > self.expires_at:
            self.status = "EXPIRED"
            return True
        return self.status == "EXPIRED"

    def to_dict(self) -> Dict[str, Any]:
        self.is_expired()
        remaining = max(0, int(self.expires_at - time.time())) if self.status == "PENDING_SCAN" else 0
        return {
            "session_id": self.session_id,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "roll_no": self.roll_no,
            "department": self.department,
            "division": self.division,
            "current_rfid_uid": self.current_rfid_uid,
            "status": self.status,
            "scanned_uid": self.scanned_uid,
            "device_id": self.device_id,
            "created_at": datetime.fromtimestamp(self.created_at, tz=timezone.utc).isoformat(),
            "expires_at": datetime.fromtimestamp(self.expires_at, tz=timezone.utc).isoformat(),
            "expires_in_seconds": remaining,
            "error": self.error
        }


class RfidAssignmentManager:
    _instance: Optional["RfidAssignmentManager"] = None

    def __init__(self):
        self._sessions: Dict[str, RfidAssignmentSession] = {}

    @classmethod
    def get_instance(cls) -> "RfidAssignmentManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start_session(
        self,
        student_id: int,
        student_name: str,
        roll_no: str,
        department: str,
        division: str,
        admin_id: str,
        current_rfid_uid: Optional[str] = None,
        device_id: Optional[str] = "GATE-READER-01",
        mode: str = "ASSIGN",
        timeout_seconds: int = 60
    ) -> RfidAssignmentSession:
        # Cancel any previous pending session for the same student or device
        for sess in self._sessions.values():
            if sess.status == "PENDING_SCAN" and (sess.student_id == student_id or sess.device_id == device_id):
                sess.status = "CANCELLED"

        session_id = str(uuid.uuid4())
        session = RfidAssignmentSession(
            session_id=session_id,
            student_id=student_id,
            student_name=student_name,
            roll_no=roll_no,
            department=department,
            division=division,
            admin_id=admin_id,
            current_rfid_uid=current_rfid_uid,
            device_id=device_id,
            mode=mode,
            timeout_seconds=timeout_seconds
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[RfidAssignmentSession]:
        session = self._sessions.get(session_id)
        if session:
            session.is_expired()
        return session

    def cancel_session(self, session_id: str) -> Optional[RfidAssignmentSession]:
        session = self.get_session(session_id)
        if session:
            session.status = "CANCELLED"
        return session

    def find_active_pending_session(self, device_id: Optional[str] = None) -> Optional[RfidAssignmentSession]:
        """
        Finds any ongoing PENDING_SCAN assignment session matching the hardware reader or campus terminal.
        """
        now = time.time()
        for session in self._sessions.values():
            if session.status == "PENDING_SCAN":
                if now > session.expires_at:
                    session.status = "EXPIRED"
                    continue
                if not device_id or not session.device_id or session.device_id in ["ALL", device_id]:
                    return session
        return None

    def record_scan(self, uid: str, device_id: Optional[str] = None) -> Optional[RfidAssignmentSession]:
        """
        Captures an incoming physical RFID card tap if an assignment session is currently pending.
        Returns the captured session, or None if no assignment session is active.
        """
        session = self.find_active_pending_session(device_id)
        if session:
            session.scanned_uid = uid.strip().upper()
            session.status = "SCANNED"
            if device_id:
                session.device_id = device_id
            return session
        return None

def get_rfid_assignment_manager() -> RfidAssignmentManager:
    return RfidAssignmentManager.get_instance()
