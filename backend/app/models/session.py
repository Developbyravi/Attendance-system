from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from app.database import Base

class AttendanceSessionModel(Base):
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    subject = Column(String(100), nullable=False)
    teacher = Column(String(100), nullable=False)
    room = Column(String(100), nullable=False)
    date = Column(String(50), nullable=False)
    start_time = Column(String(50), nullable=False)
    photo_time = Column(String(50), nullable=True)
    
    # State Machine: IDLE, RFID_COLLECTION, PHOTO_CAPTURE, AI_PROCESSING, REVIEW, COMPLETED
    status = Column(String(50), default="RFID_COLLECTION", nullable=False)
    
    total_students = Column(Integer, default=0)
    rfid_scanned_count = Column(Integer, default=0)
    ai_verified_count = Column(Integer, default=0)
    flagged_count = Column(Integer, default=0)
    present_count = Column(Integer, default=0)
    attendance_percentage = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    rfid_events = relationship("RfidEventModel", back_populates="session", cascade="all, delete-orphan")
    ai_detections = relationship("AiFaceDetectionModel", back_populates="session", cascade="all, delete-orphan")
    verifications = relationship("AttendanceVerificationModel", back_populates="session", cascade="all, delete-orphan")
    records = relationship("AttendanceRecordModel", back_populates="session", cascade="all, delete-orphan")
