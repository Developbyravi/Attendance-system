import json
from datetime import datetime, timezone
from typing import List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class TeacherModel(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True)
    teacher_id = Column(String(50), unique=True, index=True, nullable=False) # e.g. "EMP-101"
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    department = Column(String(100), default="Computer Science & Engineering")
    _assigned_divisions = Column("assigned_divisions", Text, default="[]", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    auth_user_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="teacher")
    lectures = relationship("LectureSessionModel", back_populates="teacher", cascade="all, delete-orphan")

    @property
    def assigned_divisions(self) -> List[str]:
        try:
            return json.loads(self._assigned_divisions) if self._assigned_divisions else []
        except Exception:
            return []

    @assigned_divisions.setter
    def assigned_divisions(self, val: List[str]):
        self._assigned_divisions = json.dumps(val or [])

    def __repr__(self):
        return f"<Teacher id={self.id} teacher_id='{self.teacher_id}' name='{self.name}'>"

