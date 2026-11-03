from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.database import get_db
from app.models.student import StudentModel
from app.models.daily_checkin import DailyCheckinModel
from app.models.lecture_session import LectureSessionModel
from app.models.lecture_attendance import LectureAttendanceModel
from app.core.security import get_current_student
from app.schemas.face import FaceEnrollmentResponse
from app.routers.students import execute_face_enrollment

router = APIRouter(prefix="/api/student/me", tags=["Student Portal"])

@router.post("/face-enroll", response_model=FaceEnrollmentResponse, summary="Student Self Face Enrollment")
async def student_self_enroll_face(
    files: Optional[List[UploadFile]] = File(None, description="One or more photographs of student's face"),
    file: Optional[UploadFile] = File(None, description="Single photograph captured from camera"),
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Enrolls the authenticated student's face biometrics from camera snapshot or image file.
    Enforces single usable face detection via InsightFace SCRFD-10G and ArcFace embedding generation.
    """
    upload_list: List[UploadFile] = []
    if file:
        upload_list.append(file)
    if files:
        upload_list.extend(files)

    if not upload_list:
        raise HTTPException(status_code=400, detail="No photograph file provided for face enrollment.")

    return await execute_face_enrollment(
        student_id=current_student.id,
        files=upload_list,
        db=db,
        caller_id=str(current_student.id),
        caller_role="STUDENT"
    )

@router.get("/profile")
def get_student_profile(current_student: StudentModel = Depends(get_current_student)):
    """Retrieve personal profile of authenticated student (read-only)."""
    return {
        "id": current_student.id,
        "name": current_student.name,
        "roll_no": current_student.roll_no,
        "email": current_student.email,
        "department": current_student.department,
        "year": current_student.year,
        "division": current_student.division,
        "rfid_uid": current_student.rfid_uid,
        "face_enrolled": current_student.face_enrolled,
        "created_at": current_student.created_at
    }

@router.get("/attendance")
@router.get("/me/attendance")
def get_student_attendance_summary(
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Retrieve exclusively the personal attendance records of the authenticated student.
    Returns:
    - Today's RFID check-in status
    - Today's per-lecture attendance roster
    - Overall finalized lecture attendance percentage
    """
    today_date = date.today()

    # 1. Today's Daily RFID check-in
    daily_checkin = db.query(DailyCheckinModel).filter(
        DailyCheckinModel.student_id == current_student.id,
        DailyCheckinModel.date == today_date
    ).first()

    today_checkin_data = {
        "checked_in": True if daily_checkin else False,
        "checkin_time": daily_checkin.first_scan_time.strftime("%I:%M %p") if daily_checkin and daily_checkin.first_scan_time else None,
        "scan_count": daily_checkin.scan_count if daily_checkin else 0
    }

    # 2. Today's per-lecture attendance
    today_lectures = (
        db.query(LectureAttendanceModel, LectureSessionModel)
        .join(LectureSessionModel, LectureAttendanceModel.lecture_session_id == LectureSessionModel.id)
        .filter(
            LectureAttendanceModel.student_id == current_student.id,
            LectureSessionModel.date == today_date
        )
        .all()
    )

    today_lecture_list = []
    for att, sess in today_lectures:
        today_lecture_list.append({
            "lecture_id": sess.id,
            "subject": sess.subject,
            "division": sess.division,
            "time": sess.start_time.strftime("%I:%M %p") if sess.start_time else "",
            "status": att.status,
            "verification_source": att.verification_source,
            "finalized": att.finalized
        })

    # 3. Overall finalized attendance stats across all finalized sessions
    all_finalized_attendances = (
        db.query(LectureAttendanceModel)
        .filter(
            LectureAttendanceModel.student_id == current_student.id,
            LectureAttendanceModel.finalized == True
        )
        .all()
    )

    total_finalized = len(all_finalized_attendances)
    present_count = sum(1 for a in all_finalized_attendances if a.status == "PRESENT")
    overall_pct = round((present_count / total_finalized * 100), 1) if total_finalized > 0 else 0.0

    return {
        "student_id": current_student.id,
        "roll_no": current_student.roll_no,
        "name": current_student.name,
        "division": current_student.division,
        "today_checkin": today_checkin_data,
        "today_lectures": today_lecture_list,
        "overall_attendance_percentage": overall_pct,
        "total_finalized_lectures": total_finalized,
        "present_count": present_count,
        "absent_count": total_finalized - present_count
    }
