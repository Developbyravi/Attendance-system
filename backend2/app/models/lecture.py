from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Date, Time, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class LectureSessionModel(Base):
    __tablename__ = "lecture_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(150), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), nullable=True)
    division = Column(String(50), nullable=False, index=True)
    division_id = Column(Integer, ForeignKey("divisions.id", ondelete="SET NULL"), nullable=True)
    date = Column(Date, default=lambda: datetime.now(timezone.utc).date(), nullable=False, index=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    classroom = Column(String(50), default="Room 101")
    status = Column(String(50), default="SCHEDULED", nullable=False) # SCHEDULED, IN_PROGRESS, REVIEW_PENDING, FINALIZED
    classroom_photo_url = Column(String(500), nullable=True)
    overlay_image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    teacher = relationship("TeacherModel", back_populates="lectures")
    division_rel = relationship("ClassDivisionModel", back_populates="lectures")
    subject_rel = relationship("SubjectModel", back_populates="lectures")
    attendances = relationship("LectureAttendanceModel", back_populates="lecture_session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LectureSession id={self.id} subject='{self.subject}' div='{self.division}' status='{self.status}'>"

