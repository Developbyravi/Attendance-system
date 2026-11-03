from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class AttendanceVerificationModel(Base):
    __tablename__ = "attendance_verifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=True) # None for unknown face
    rfid_status = Column(Boolean, default=False)
    ai_status = Column(Boolean, default=False)
    ai_confidence = Column(Float, default=0.0)
    
    # Statuses: VERIFIED_PRESENT, RFID_ONLY, AI_ONLY, UNKNOWN, ABSENT
    final_status = Column(String(50), nullable=False)
    flag_reason = Column(String(255), nullable=True)
    teacher_resolution = Column(String(50), nullable=True) # "CONFIRM_PRESENT", "MARK_ABSENT", "IGNORE"
    resolution_reason = Column(String(255), nullable=True)

    session = relationship("AttendanceSessionModel", back_populates="verifications")
    student = relationship("StudentModel")
