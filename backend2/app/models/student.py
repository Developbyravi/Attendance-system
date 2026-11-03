from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class StudentModel(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True)
    roll_no = Column(String(50), index=True, nullable=False) # e.g. "10"
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    department = Column(String(100), default="Computer Science & Engineering")
    year = Column(String(50), default="3rd Year")
    division = Column(String(50), default="A", index=True)
    division_id = Column(Integer, ForeignKey("divisions.id", ondelete="SET NULL"), nullable=True)
    rfid_uid = Column(String(50), unique=True, index=True, nullable=True)
    face_enrolled = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    auth_user_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="student")
    division_rel = relationship("ClassDivisionModel", back_populates="students")
    face_embeddings = relationship("FaceEmbeddingModel", back_populates="student", cascade="all, delete-orphan")
    daily_checkins = relationship("DailyCheckinModel", back_populates="student", cascade="all, delete-orphan")
    attendances = relationship("LectureAttendanceModel", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student id={self.id} roll='{self.roll_no}' name='{self.name}' div='{self.division}'>"

