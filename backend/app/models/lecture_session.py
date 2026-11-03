from datetime import datetime, timezone, date
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class LectureSessionModel(Base):
    __tablename__ = "lecture_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False, index=True)
    subject = Column(String(100), nullable=False)
    division = Column(String(50), nullable=False)
    date = Column(Date, nullable=False, index=True, default=date.today)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    status = Column(String(50), default="ACTIVE") # ACTIVE, VERIFYING, FINALIZED, CANCELLED
    classroom_photo_url = Column(String(500), nullable=True)
    overlay_image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    teacher = relationship("TeacherModel")
    attendances = relationship("LectureAttendanceModel", back_populates="lecture_session", cascade="all, delete-orphan")
