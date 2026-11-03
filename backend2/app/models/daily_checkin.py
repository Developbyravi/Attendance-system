from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class DailyCheckinModel(Base):
    __tablename__ = "daily_checkins"
    __table_args__ = (
        UniqueConstraint("student_id", "date", name="uq_student_daily_checkin"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, default=lambda: datetime.now(timezone.utc).date(), nullable=False, index=True)
    check_in_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    rfid_uid = Column(String(50), nullable=False, index=True)
    device_id = Column(String(50), default="GATE-READER-01", nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)

    # Relationships
    student = relationship("StudentModel", back_populates="daily_checkins")

    def __repr__(self):
        return f"<DailyCheckin id={self.id} student_id={self.student_id} date={self.date}>"

