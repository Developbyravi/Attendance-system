from datetime import datetime, timezone, date
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class DailyCheckinModel(Base):
    __tablename__ = "daily_checkins"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True, default=date.today)
    rfid_uid = Column(String(50), nullable=False)
    first_scan_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_scan_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    scan_count = Column(Integer, default=1)
    device_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    student = relationship("StudentModel")

    __table_args__ = (
        UniqueConstraint('student_id', 'date', name='uq_daily_checkin_student_date'),
    )
