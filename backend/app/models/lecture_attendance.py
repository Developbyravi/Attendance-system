from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class LectureAttendanceModel(Base):
    __tablename__ = "lecture_attendances"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lecture_session_id = Column(Integer, ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False) # PRESENT, ABSENT, FLAGGED
    verification_source = Column(String(50), nullable=False) # RFID_AND_AI, RFID_ONLY, AI_ONLY, TEACHER_CONFIRMED, TEACHER_MARKED_ABSENT
    ai_confidence = Column(Float, nullable=True)
    rfid_checked_in = Column(Boolean, default=False)
    ai_detected = Column(Boolean, default=False)
    teacher_action = Column(String(50), nullable=True) # CONFIRMED_PRESENT, MARKED_ABSENT, None
    finalized = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    lecture_session = relationship("LectureSessionModel", back_populates="attendances")
    student = relationship("StudentModel")

    __table_args__ = (
        UniqueConstraint('lecture_session_id', 'student_id', name='uq_lecture_attendance_session_student'),
    )
