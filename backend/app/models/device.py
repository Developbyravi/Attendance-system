from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class DeviceModel(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(100), unique=True, index=True, nullable=False)
    device_name = Column(String(150), nullable=False)
    location = Column(String(150), nullable=False)
    ip_address = Column(String(50), nullable=True)
    mac_address = Column(String(50), nullable=True)
    status = Column(String(50), default="online")
    last_ping = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    firmware_version = Column(String(50), default="v2.4.1-esp8266")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
