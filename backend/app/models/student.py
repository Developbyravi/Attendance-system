from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class StudentModel(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    roll_no = Column(String(50), unique=True, index=True, nullable=False)
    department = Column(String(100), nullable=False)
    year = Column(String(50), nullable=False)
    division = Column(String(50), nullable=True, default="A")
    email = Column(String(100), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    rfid_uid = Column(String(50), unique=True, index=True, nullable=False)
    auth_user_id = Column(String(100), unique=True, nullable=True) # Supabase auth.users UUID
    face_enrolled = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    face_embeddings = relationship("FaceEmbeddingModel", back_populates="student", cascade="all, delete-orphan")
