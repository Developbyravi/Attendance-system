from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class ClassDivisionModel(Base):
    __tablename__ = "divisions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, index=True) # e.g. "A", "B"
    code = Column(String(50), nullable=True, unique=True, index=True) # e.g. "CSE-A-Y3"
    academic_year = Column(String(50), default="2026-2027")
    semester = Column(String(50), default="5")
    department = Column(String(100), default="Computer Science & Engineering")
    total_students = Column(Integer, default=0)
    class_teacher = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    students = relationship("StudentModel", back_populates="division_rel")
    lectures = relationship("LectureSessionModel", back_populates="division_rel")

    def __repr__(self):
        return f"<Division id={self.id} name='{self.name}' dept='{self.department}'>"

