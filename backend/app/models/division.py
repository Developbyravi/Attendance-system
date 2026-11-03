from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class DivisionModel(Base):
    __tablename__ = "divisions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    department = Column(String(100), nullable=False)
    academic_year = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
