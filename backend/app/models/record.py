from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class AttendanceRecordModel(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    final_status = Column(String(50), nullable=False) # VERIFIED_PRESENT, RFID_ONLY, AI_ONLY, ABSENT
    is_present = Column(Boolean, default=False)
    verified_by = Column(String(50), default="AUTO") # AUTO | TEACHER
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("AttendanceSessionModel", back_populates="records")
    student = relationship("StudentModel")
