import uuid
from datetime import datetime, date, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.student import StudentModel
from app.models.daily_checkin import DailyCheckinModel
from app.core.exceptions import EntityNotFoundError, DuplicateEntityError, SmartAttendException

# In-memory store for interactive card assignment sessions
ACTIVE_ASSIGNMENT_SESSIONS: Dict[str, Dict[str, Any]] = {}

class RFIDService:
    @staticmethod
    def record_daily_checkin(
        db: Session,
        rfid_uid: str,
        device_id: str = "GATE-READER-01"
    ) -> Dict[str, Any]:
        """
        Processes physical morning campus gate tap.
        - Validates student existence and active status.
        - Idempotent: duplicate taps on the same day return ALREADY_CHECKED_IN.
        """
        clean_uid = rfid_uid.replace(":", "").replace("-", "").strip().upper()
        formatted_colon_uid = ":".join([clean_uid[i:i+2] for i in range(0, len(clean_uid), 2)])

        # 1. Check if an active interactive RFID assignment session is pending for this reader
        for sess_id, sess in ACTIVE_ASSIGNMENT_SESSIONS.items():
            if sess.get("status") == "PENDING_SCAN":
                expires_at = datetime.fromisoformat(sess["expires_at"])
                if datetime.now(timezone.utc) < expires_at:
                    sess["status"] = "SCANNED"
                    sess["scanned_uid"] = clean_uid
                    return {
                        "status": "assignment_captured",
                        "mode": "assignment",
                        "session_id": sess_id,
                        "scanned_uid": clean_uid,
                        "message": f"Card {clean_uid} captured for student {sess.get('student_name')}."
                    }

        # 2. Normal Mode: Look up student by clean UID, colon-formatted UID, or original UID
        from sqlalchemy import or_
        student = db.query(StudentModel).filter(
            or_(
                StudentModel.rfid_uid == clean_uid,
                StudentModel.rfid_uid == formatted_colon_uid,
                StudentModel.rfid_uid == rfid_uid.strip(),
                StudentModel.rfid_uid == rfid_uid.strip().upper()
            ),
            StudentModel.is_active == True
        ).first()

        if not student:
            raise EntityNotFoundError("Active Student with RFID card", clean_uid)

        today_date = datetime.now(timezone.utc).date()
        now_dt = datetime.now(timezone.utc)

        existing_checkin = db.query(DailyCheckinModel).filter(
            DailyCheckinModel.student_id == student.id,
            DailyCheckinModel.date == today_date
        ).first()

        student_summary = {
            "id": student.id,
            "name": student.name,
            "roll_number": student.roll_no,
            "division_name": student.division,
            "department": student.department
        }

        if existing_checkin:
            return {
                "status": "ALREADY_CHECKED_IN",
                "message": f"Student '{student.name}' has already checked in for today.",
                "student": student_summary,
                "check_in_time": existing_checkin.check_in_time.isoformat(),
                "date": today_date.isoformat()
            }

        new_checkin = DailyCheckinModel(
            student_id=student.id,
            date=today_date,
            check_in_time=now_dt,
            rfid_uid=student.rfid_uid or clean_uid,
            device_id=device_id or "GATE-READER-01",
            is_verified=True
        )
        db.add(new_checkin)
        db.commit()
        db.refresh(new_checkin)

        return {
            "status": "SUCCESS",
            "message": f"Daily RFID check-in verified for '{student.name}'.",
            "student": student_summary,
            "check_in_time": new_checkin.check_in_time.isoformat(),
            "date": today_date.isoformat()
        }

    @staticmethod
    def start_assignment_session(
        db: Session,
        student_id: int,
        device_id: str = "GATE-READER-01",
        timeout_seconds: int = 60
    ) -> Dict[str, Any]:
        """Initiates an interactive card assignment window on reader."""
        student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
        if not student:
            raise EntityNotFoundError("Student", student_id)

        session_id = uuid.uuid4().hex[:16]
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=timeout_seconds)

        session_data = {
            "session_id": session_id,
            "student_id": student.id,
            "student_name": student.name,
            "roll_no": student.roll_no,
            "department": student.department,
            "division": student.division,
            "current_rfid_uid": student.rfid_uid,
            "status": "PENDING_SCAN",
            "scanned_uid": None,
            "device_id": device_id,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "expires_in_seconds": timeout_seconds,
            "error": None
        }

        ACTIVE_ASSIGNMENT_SESSIONS[session_id] = session_data
        return session_data

    @staticmethod
    def get_assignment_session(session_id: str) -> Dict[str, Any]:
        """Polls status of card scan session."""
        session_data = ACTIVE_ASSIGNMENT_SESSIONS.get(session_id)
        if not session_data:
            raise EntityNotFoundError("Assignment Session", session_id)

        # Check expiration
        expires_at = datetime.fromisoformat(session_data["expires_at"])
        remaining = int((expires_at - datetime.now(timezone.utc)).total_seconds())

        if remaining <= 0 and session_data["status"] == "PENDING_SCAN":
            session_data["status"] = "EXPIRED"
            session_data["expires_in_seconds"] = 0
        else:
            session_data["expires_in_seconds"] = max(0, remaining)

        return session_data

    @staticmethod
    def cancel_assignment_session(session_id: str) -> Dict[str, Any]:
        """Cancels an active card scan session and cleans up memory."""
        session_data = ACTIVE_ASSIGNMENT_SESSIONS.pop(session_id, None)
        return {"status": "cancelled", "session_id": session_id}

    @staticmethod
    def confirm_assignment(
        db: Session,
        session_id: str,
        student_id: int,
        rfid_uid: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Binds scanned RFID card UID to student record."""
        clean_uid = rfid_uid.strip().upper()

        # Check if card is already assigned to a DIFFERENT student
        existing = db.query(StudentModel).filter(
            StudentModel.rfid_uid == clean_uid,
            StudentModel.id != student_id
        ).first()
        if existing:
            raise DuplicateEntityError("RFID Card", "UID", clean_uid)

        student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
        if not student:
            raise EntityNotFoundError("Student", student_id)

        prev_uid = student.rfid_uid
        student.rfid_uid = clean_uid
        db.commit()
        db.refresh(student)

        # Close session
        if session_id in ACTIVE_ASSIGNMENT_SESSIONS:
            ACTIVE_ASSIGNMENT_SESSIONS[session_id]["status"] = "CONFIRMED"
            ACTIVE_ASSIGNMENT_SESSIONS[session_id]["scanned_uid"] = clean_uid

        return {
            "status": "success",
            "action": "ASSIGNED",
            "student_id": student.id,
            "roll_no": student.roll_no,
            "student_name": student.name,
            "rfid_uid": clean_uid,
            "previous_rfid_uid": prev_uid,
            "session_id": session_id
        }

    @staticmethod
    def deactivate_card(
        db: Session,
        student_id: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clears student RFID card UID."""
        student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
        if not student:
            raise EntityNotFoundError("Student", student_id)

        old_uid = student.rfid_uid
        student.rfid_uid = None
        db.commit()

        return {
            "status": "success",
            "action": "DEACTIVATED",
            "student_id": student.id,
            "student_name": student.name,
            "roll_no": student.roll_no,
            "deactivated_rfid_uid": old_uid
        }

