import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import relationship
from app.database import Base

class LectureAttendanceModel(Base):
    __tablename__ = "lecture_attendances"
    __table_args__ = (
        UniqueConstraint("lecture_session_id", "student_id", name="uq_lecture_student_attendance"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lecture_session_id = Column(Integer, ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True) # PRESENT, FLAGGED, PENDING, ABSENT
    verification_source = Column(String(50), default="UNVERIFIED", nullable=False) # RFID_AND_AI, AI_ONLY, RFID_ONLY, AMBIGUOUS_AI, TEACHER_CONFIRMED, TEACHER_MANUAL, FINALIZED_ABSENT, UNVERIFIED
    ai_confidence = Column(Float, nullable=True)
    rfid_checked_in = Column(Boolean, default=False, nullable=False)
    ai_detected = Column(Boolean, default=False, nullable=False)
    teacher_action = Column(String(255), nullable=True)
    finalized = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    lecture_session = relationship("LectureSessionModel", back_populates="attendances")
    student = relationship("StudentModel", back_populates="attendances")

    def __repr__(self):
        return f"<Attendance id={self.id} lecture={self.lecture_session_id} student={self.student_id} status='{self.status}'>"

class AttendanceAuditLogModel(Base):
    __tablename__ = "attendance_audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), nullable=True, index=True)
    role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=True)
    _details = Column("details", Text, default="{}", nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    @property
    def details_dict(self):
        try:
            return json.loads(self._details)
        except Exception:
            return {}

    @details_dict.setter
    def details_dict(self, val):
        self._details = json.dumps(val or {})

class DeviceModel(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(50), unique=True, index=True, nullable=False)
    device_name = Column(String(100), nullable=False)
    location = Column(String(100), default="Campus Main Entrance")
    ip_address = Column(String(50), nullable=True)
    mac_address = Column(String(50), nullable=True)
    status = Column(String(50), default="online") # online, offline, maintenance
    last_ping = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    firmware_version = Column(String(50), default="1.0.0-rc1")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

