from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.teacher import TeacherModel
from app.models.user import UserModel
from app.models.lecture import LectureSessionModel
from app.schemas.lecture import (
    LectureCreate,
    LectureSessionResponse,
    LectureVerificationSummary,
    AttendanceReviewItem,
    StudentAttendanceUpdate,
    FlagResolutionRequest,
    LectureAttendanceItem
)
from app.services.lecture_service import LectureService
from app.services.attendance_service import AttendanceService
from app.core.permissions import require_teacher, get_current_teacher, get_current_user

router = APIRouter(prefix="/lectures", tags=["Lectures"])

def _assert_lecture_teacher_access(db: Session, lecture_id: int, current_teacher: TeacherModel):
    lecture = db.query(LectureSessionModel).filter(LectureSessionModel.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail=f"Lecture session #{lecture_id} not found.")
    if lecture.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied. You can only view and manage lecture sessions assigned to you."
        )
    return lecture

@router.get("", response_model=List[LectureSessionResponse], summary="List Lectures")
def list_lectures(
    teacher_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)
):
    tid = int(teacher_id) if teacher_id and str(teacher_id).isdigit() else None
    return LectureService.list_lectures(db, teacher_id=tid, target_date=date)

@router.post("", response_model=LectureSessionResponse, summary="Schedule / Start Lecture Session")
def create_lecture(
    payload: LectureCreate,
    db: Session = Depends(get_db),
    current_teacher: TeacherModel = Depends(get_current_teacher)
):
    return LectureService.create(db, current_teacher.id, payload.model_dump())

@router.get("/{lecture_id}", response_model=LectureSessionResponse, summary="Get Lecture Details & Roster")
def get_lecture(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return LectureService.get_by_id(db, lecture_id)

@router.post("/{lecture_id}/photo", response_model=LectureVerificationSummary, summary="Process Classroom Photo & Cross-Verify Attendance")
@router.post("/{lecture_id}/verify-photo", response_model=LectureVerificationSummary, summary="Alias for Photo Verification")
async def process_classroom_photo(
    lecture_id: int,
    file: Optional[UploadFile] = File(None),
    photo: Optional[UploadFile] = File(None),
    threshold: float = Query(0.70, ge=0.0, le=1.0),
    auto_mark_absent: Optional[bool] = Query(False),
    db: Session = Depends(get_db),
    current_teacher: TeacherModel = Depends(get_current_teacher)
):
    _assert_lecture_teacher_access(db, lecture_id, current_teacher)
    target = file or photo
    if not target:
        raise HTTPException(status_code=400, detail="Classroom photograph file is required.")

    file_bytes = await target.read()
    return AttendanceService.process_lecture_photo(
        db=db,
        lecture_id=lecture_id,
        image_bytes=file_bytes,
        filename=target.filename,
        threshold=threshold,
        auto_mark_absent=bool(auto_mark_absent)
    )

@router.get("/{lecture_id}/review", response_model=List[AttendanceReviewItem], summary="Get Attendance Review Roster")
def get_lecture_review_roster(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_teacher: TeacherModel = Depends(get_current_teacher)
):
    _assert_lecture_teacher_access(db, lecture_id, current_teacher)
    return AttendanceService.get_review_roster(db, lecture_id)

@router.patch("/{lecture_id}/students/{student_id}", summary="Override Student Attendance Status")
def update_student_attendance(
    lecture_id: int,
    student_id: int,
    payload: StudentAttendanceUpdate,
    db: Session = Depends(get_db),
    current_teacher: TeacherModel = Depends(get_current_teacher)
):
    _assert_lecture_teacher_access(db, lecture_id, current_teacher)
    return AttendanceService.update_student_attendance(
        db=db,
        lecture_id=lecture_id,
        student_id=student_id,
        status=payload.status,
        reason=payload.reason,
        actor_id=str(current_teacher.id),
        actor_role="TEACHER"
    )

@router.post("/{lecture_id}/resolve-flag", summary="Teacher Resolves Ambiguity or Flag")
def resolve_flag(
    lecture_id: int,
    payload: FlagResolutionRequest,
    db: Session = Depends(get_db),
    current_teacher: TeacherModel = Depends(get_current_teacher)
):
    _assert_lecture_teacher_access(db, lecture_id, current_teacher)
    status_map = {
        "CONFIRM_PRESENT": "PRESENT",
        "MARK_ABSENT": "ABSENT"
    }
    new_status = status_map.get(payload.action.upper(), "PRESENT")
    return AttendanceService.update_student_attendance(
        db=db,
        lecture_id=lecture_id,
        student_id=payload.student_id,
        status=new_status,
        reason=f"TEACHER_{payload.action.upper()}",
        actor_id=str(current_teacher.id),
        actor_role="TEACHER"
    )

@router.post("/{lecture_id}/finalize", summary="Finalize Lecture Attendance (Immutability Lock)")
def finalize_lecture(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_teacher: TeacherModel = Depends(get_current_teacher)
):
    _assert_lecture_teacher_access(db, lecture_id, current_teacher)
    return AttendanceService.finalize_lecture(
        db=db,
        lecture_id=lecture_id,
        actor_id=str(current_teacher.id),
        actor_role="TEACHER"
    )

