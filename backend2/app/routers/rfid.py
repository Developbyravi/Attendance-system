from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.attendance import DeviceModel
from app.services.rfid_service import RFIDService
from app.core.permissions import require_admin

router = APIRouter(tags=["Hardware RFID & Kiosk"])

class AssignmentStartRequest(BaseModel):
    student_id: int
    mode: Optional[str] = "ASSIGN"
    device_id: Optional[str] = "GATE-READER-01"
    timeout_seconds: Optional[int] = 60

class AssignmentConfirmRequest(BaseModel):
    session_id: str
    student_id: int
    rfid_uid: str
    reason: Optional[str] = None

class CancelRequest(BaseModel):
    session_id: str

class DeactivateCardRequest(BaseModel):
    student_id: int
    reason: Optional[str] = None

class KioskScanRequest(BaseModel):
    rfid_uid: str
    device_id: Optional[str] = "GATE-READER-01"

class DeviceCreate(BaseModel):
    device_id: str
    device_name: str
    location: Optional[str] = "Campus Main Entrance"

@router.post("/rfid/assignment/start", summary="Start Hardware RFID Assignment Session")
def start_rfid_assignment(
    payload: AssignmentStartRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    return RFIDService.start_assignment_session(
        db=db,
        student_id=payload.student_id,
        device_id=payload.device_id or "GATE-READER-01",
        timeout_seconds=payload.timeout_seconds or 60
    )

@router.get("/rfid/assignment/session/{session_id}", summary="Get Assignment Session Status")
def get_session_status(session_id: str):
    return RFIDService.get_assignment_session(session_id)

@router.post("/rfid/assignment/confirm", summary="Confirm RFID Assignment")
def confirm_rfid_assignment(
    payload: AssignmentConfirmRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    return RFIDService.confirm_assignment(
        db=db,
        session_id=payload.session_id,
        student_id=payload.student_id,
        rfid_uid=payload.rfid_uid,
        reason=payload.reason
    )

@router.post("/rfid/assignment/cancel", summary="Cancel RFID Assignment")
def cancel_rfid_assignment(payload: CancelRequest):
    return RFIDService.cancel_assignment_session(payload.session_id)

@router.post("/rfid/deactivate", summary="Deactivate Student RFID Card")
def deactivate_rfid(
    payload: DeactivateCardRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    return RFIDService.deactivate_card(db, payload.student_id, payload.reason)

# ── KIOSK GATEWAY ENDPOINTS ──

@router.get("/kiosk/status", summary="Get Kiosk Gateway Status")
def get_kiosk_status():
    return {
        "status": "online",
        "timestamp": datetime.now(timezone.utc).strftime("%I:%M:%S %p")
    }

@router.post("/kiosk/scan", summary="Process Kiosk Hardware Scan")
def kiosk_scan(payload: KioskScanRequest, db: Session = Depends(get_db)):
    return RFIDService.record_daily_checkin(
        db=db,
        rfid_uid=payload.rfid_uid,
        device_id=payload.device_id or "GATE-READER-01"
    )

# ── DEVICE MANAGEMENT ENDPOINTS ──

@router.get("/devices", summary="List IoT Devices")
def list_devices(db: Session = Depends(get_db)):
    devices = db.query(DeviceModel).all()
    if not devices:
        # Seed default reader if none exists
        default_dev = DeviceModel(
            device_id="GATE-READER-01",
            device_name="Main Campus RFID Gate",
            location="Campus Gate 1",
            status="online",
            firmware_version="v2.1.0-esp8266"
        )
        db.add(default_dev)
        db.commit()
        db.refresh(default_dev)
        devices = [default_dev]

    return [
        {
            "id": d.id,
            "device_id": d.device_id,
            "device_name": d.device_name,
            "location": d.location,
            "ip_address": d.ip_address,
            "mac_address": d.mac_address,
            "status": d.status,
            "last_ping": d.last_ping.isoformat() if d.last_ping else None,
            "firmware_version": d.firmware_version
        }
        for d in devices
    ]

@router.post("/devices", summary="Register IoT Device")
def register_device(
    payload: DeviceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    dev = DeviceModel(
        device_id=payload.device_id,
        device_name=payload.device_name,
        location=payload.location or "Main Campus Gate",
        status="online"
    )
    db.add(dev)
    db.commit()
    db.refresh(dev)
    return {
        "id": dev.id,
        "device_id": dev.device_id,
        "device_name": dev.device_name,
        "location": dev.location,
        "status": dev.status
    }

