from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="STUDENT") # ADMIN, TEACHER, STUDENT, PARENT
    is_active = Column(Boolean, default=True, nullable=False)
    auth_user_id = Column(String(100), nullable=True, index=True) # Supabase UUID
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    teacher = relationship("TeacherModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    student = relationship("StudentModel", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email='{self.email}' role='{self.role}'>"

