from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True) # Teacher ID, Student ID, or Admin
    role = Column(String(50), nullable=False) # TEACHER, ADMIN, SYSTEM
    action = Column(String(100), nullable=False) # RESOLVE_FLAG, FINALIZE_LECTURE, ENROLL_FACE, etc.
    entity_type = Column(String(50), nullable=False) # LECTURE_ATTENDANCE, LECTURE_SESSION, STUDENT
    entity_id = Column(String(50), nullable=False)
    details = Column(Text, nullable=True) # JSON details
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
