from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class RfidEventModel(Base):
    __tablename__ = "rfid_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    rfid_uid = Column(String(50), nullable=False)
    timestamp = Column(String(50), nullable=False)
    scan_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("AttendanceSessionModel", back_populates="rfid_events")
    student = relationship("StudentModel")
