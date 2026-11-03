from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class ParentModel(Base):
    __tablename__ = "parents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    auth_user_id = Column(String(100), unique=True, nullable=True) # Supabase auth.users UUID
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    children = relationship("ParentStudentModel", back_populates="parent", cascade="all, delete-orphan")


class ParentStudentModel(Base):
    __tablename__ = "parent_students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey("parents.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(50), default="GUARDIAN") # FATHER, MOTHER, GUARDIAN
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    parent = relationship("ParentModel", back_populates="children")
    student = relationship("StudentModel")

    __table_args__ = (
        UniqueConstraint('parent_id', 'student_id', name='uq_parent_student'),
    )
