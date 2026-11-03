from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.daily_checkin import DailyCheckinModel
from app.models.student import StudentModel
from app.schemas.attendance import DailyCheckinRequest, DailyCheckinResponse, DailyCheckInRecord
from app.services.rfid_service import RFIDService
from app.core.permissions import require_teacher

router = APIRouter(tags=["Daily Attendance & RFID"])

@router.post("/attendance/rfid", response_model=DailyCheckinResponse, summary="Daily RFID Morning Campus Check-In")
def record_rfid_checkin(
    payload: DailyCheckinRequest,
    db: Session = Depends(get_db)
):
    """
    Physical morning RFID card scan at gate or campus kiosk reader.
    Idempotent: Duplicate scans on same day return ALREADY_CHECKED_IN.
    """
    return RFIDService.record_daily_checkin(
        db=db,
        rfid_uid=payload.rfid_uid,
        device_id=payload.device_id or "GATE-READER-01"
    )

@router.get("/daily-checkins", response_model=List[DailyCheckInRecord], summary="List Daily RFID Check-In Logs")
def list_daily_checkins(
    division_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_teacher)
):
    q = db.query(DailyCheckinModel).join(StudentModel)

    if date:
        try:
            target_d = datetime.strptime(str(date)[:10], "%Y-%m-%d").date()
            q = q.filter(DailyCheckinModel.date == target_d)
        except Exception:
            pass
    else:
        today_d = datetime.now(timezone.utc).date()
        q = q.filter(DailyCheckinModel.date == today_d)

    if division_id:
        clean_div = division_id.replace("Division ", "").replace("Div ", "").strip()
        q = q.filter(
            or_(
                StudentModel.division == clean_div,
                StudentModel.division == f"Div {clean_div}",
                StudentModel.division == f"Division {clean_div}"
            )
        )

    logs = q.order_by(DailyCheckinModel.check_in_time.desc()).all()

    return [
        {
            "id": log.id,
            "student_id": log.student_id,
            "student_name": log.student.name if log.student else "Student",
            "roll_number": log.student.roll_no if log.student else "",
            "division_name": log.student.division if log.student else "A",
            "rfid_uid": log.rfid_uid,
            "device_id": log.device_id,
            "check_in_time": log.check_in_time.strftime("%I:%M %p"),
            "is_verified": log.is_verified
        }
        for log in logs
    ]

