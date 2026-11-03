from datetime import datetime, timezone, date
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.student import StudentModel
from app.models.teacher import TeacherModel
from app.models.daily_checkin import DailyCheckinModel
from app.schemas.daily_checkin import (
    RfidCheckinRequest,
    DailyCheckinResponse,
    DailyCheckinSummaryResponse,
    DailyCheckinSummaryStudent
)
from app.core.security import get_current_teacher, verify_device_or_teacher

router = APIRouter(prefix="/api/attendance", tags=["Attendance & Daily RFID Check-in"])

@router.post("/rfid", response_model=DailyCheckinResponse, summary="Record Daily RFID Check-in Event")
def record_daily_rfid_checkin(
    req: RfidCheckinRequest,
    db: Session = Depends(get_db),
    device_or_teacher: dict = Depends(verify_device_or_teacher)
):
    """
    Records a student's daily RFID check-in for presence tracking.
    - Does NOT require session_id.
    - If student is scanning for the first time today, creates a DailyCheckin record with status CHECKED_IN.
    - If already scanned today, updates last_scan_time, increments scan_count, and returns ALREADY_CHECKED_IN.
    """
    normalized_uid = req.rfid_uid.strip().upper() if req.rfid_uid else ""
    student = db.query(StudentModel).filter(
        (StudentModel.rfid_uid == normalized_uid) | (StudentModel.rfid_uid == req.rfid_uid)
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with RFID UID '{req.rfid_uid}' not found.")

    if not student.is_active:
        raise HTTPException(status_code=400, detail="Student account is inactive.")

    today_date = date.today()
    now_dt = datetime.now(timezone.utc)
    scan_time_str = now_dt.strftime("%H:%M:%S")

    checkin = db.query(DailyCheckinModel).filter(
        DailyCheckinModel.student_id == student.id,
        DailyCheckinModel.date == today_date
    ).first()

    if checkin:
        checkin.last_scan_time = now_dt
        checkin.scan_count += 1
        db.commit()
        status_res = "ALREADY_CHECKED_IN"
    else:
        checkin = DailyCheckinModel(
            student_id=student.id,
            date=today_date,
            rfid_uid=req.rfid_uid,
            first_scan_time=now_dt,
            last_scan_time=now_dt,
            scan_count=1,
            device_id=req.device_id
        )
        db.add(checkin)
        db.commit()
        db.refresh(checkin)
        status_res = "CHECKED_IN"

    return DailyCheckinResponse(
        id=checkin.id,
        student_id=student.id,
        student_name=student.name,
        roll_no=student.roll_no,
        date=today_date.isoformat(),
        scan_time=scan_time_str,
        status=status_res
    )

@router.get("/daily-checkins", response_model=DailyCheckinSummaryResponse, summary="Get Today's Daily Check-in Summary")
def get_daily_checkins_summary(
    date_val: Optional[str] = None,
    db: Session = Depends(get_db),
    current_teacher: TeacherModel = Depends(get_current_teacher)
):
    """
    Teacher endpoint returning list of daily checked-in students and overall metrics.
    """
    target_date = date.fromisoformat(date_val) if date_val else date.today()
    total_active_students = db.query(StudentModel).filter(StudentModel.is_active == True).count()

    checkins = db.query(DailyCheckinModel).filter(DailyCheckinModel.date == target_date).all()
    checked_in_count = len(checkins)

    pct = round((checked_in_count / total_active_students * 100), 1) if total_active_students > 0 else 0.0

    students_list = []
    for c in checkins:
        st = c.student
        if st:
            scan_time_str = c.first_scan_time.strftime("%H:%M:%S") if c.first_scan_time else ""
            students_list.append(DailyCheckinSummaryStudent(
                id=c.id,
                student_id=st.id,
                student_name=st.name,
                roll_no=st.roll_no,
                department=st.department,
                division=st.division or "A",
                scan_time=scan_time_str,
                scan_count=c.scan_count
            ))

    return DailyCheckinSummaryResponse(
        date=target_date.isoformat(),
        checked_in=checked_in_count,
        total_students=total_active_students,
        percentage=pct,
        students=students_list
    )
