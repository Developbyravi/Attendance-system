from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class SubjectModel(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False, index=True)
    code = Column(String(50), nullable=True, unique=True, index=True)
    department = Column(String(100), default="Computer Science & Engineering")
    semester = Column(String(50), default="5")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    lectures = relationship("LectureSessionModel", back_populates="subject_rel")

    def __repr__(self):
        return f"<Subject id={self.id} code='{self.code}' name='{self.name}'>"

