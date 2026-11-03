from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserModel
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse, StudentProfileResponse
from app.schemas.face import FaceEnrollmentResponse
from app.services.student_service import StudentService
from app.services.dashboard_service import DashboardService
from app.core.permissions import require_teacher, require_admin, require_student, get_current_user

router = APIRouter(tags=["Students"])

@router.get("/students", response_model=List[StudentResponse], summary="List Students")
def list_students(
    division_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)
):
    students = StudentService.get_all(db, division_id=division_id, query=q)
    return [
        {
            "id": s.id,
            "roll_no": s.roll_no,
            "roll_number": s.roll_no,
            "name": s.name,
            "full_name": s.name,
            "email": s.email,
            "department": s.department,
            "year": s.year,
            "division": s.division,
            "division_id": s.division,
            "division_name": s.division,
            "class_name": f"Div {s.division}",
            "rfid_uid": s.rfid_uid,
            "face_enrolled": s.face_enrolled,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in students
    ]

@router.post("/students", response_model=StudentResponse, summary="Create Student")
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):
    student = StudentService.create(db, payload.model_dump())
    return {
        "id": student.id,
        "roll_no": student.roll_no,
        "roll_number": student.roll_no,
        "name": student.name,
        "full_name": student.name,
        "email": student.email,
        "department": student.department,
        "year": student.year,
        "division": student.division,
        "division_id": student.division,
        "division_name": student.division,
        "class_name": f"Div {student.division}",
        "rfid_uid": student.rfid_uid,
        "face_enrolled": student.face_enrolled,
        "is_active": student.is_active,
        "created_at": student.created_at.isoformat() if student.created_at else None
    }

@router.get("/students/{student_id}", response_model=StudentResponse, summary="Get Student Details")
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)
):
    student = StudentService.get_by_id(db, student_id)
    return {
        "id": student.id,
        "roll_no": student.roll_no,
        "roll_number": student.roll_no,
        "name": student.name,
        "full_name": student.name,
        "email": student.email,
        "department": student.department,
        "year": student.year,
        "division": student.division,
        "division_id": student.division,
        "division_name": student.division,
        "class_name": f"Div {student.division}",
        "rfid_uid": student.rfid_uid,
        "face_enrolled": student.face_enrolled,
        "is_active": student.is_active,
        "created_at": student.created_at.isoformat() if student.created_at else None
    }

@router.put("/students/{student_id}", response_model=StudentResponse, summary="Update Student")
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):
    student = StudentService.update(db, student_id, payload.model_dump(exclude_unset=True))
    return {
        "id": student.id,
        "roll_no": student.roll_no,
        "roll_number": student.roll_no,
        "name": student.name,
        "full_name": student.name,
        "email": student.email,
        "department": student.department,
        "year": student.year,
        "division": student.division,
        "division_id": student.division,
        "division_name": student.division,
        "class_name": f"Div {student.division}",
        "rfid_uid": student.rfid_uid,
        "face_enrolled": student.face_enrolled,
        "is_active": student.is_active,
        "created_at": student.created_at.isoformat() if student.created_at else None
    }

@router.patch("/students/{student_id}/deactivate", summary="Deactivate Student Account")
def deactivate_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):
    StudentService.deactivate(db, student_id)
    return {"status": "success", "message": f"Student #{student_id} successfully deactivated."}

@router.post("/students/{student_id}/face-enroll", response_model=FaceEnrollmentResponse, summary="Enroll Face Biometrics (Admin / Faculty)")
async def enroll_student_face(
    student_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)
):
    file_bytes = await file.read()
    res = StudentService.enroll_face(db, student_id, file_bytes, file.filename)
    return res

# ── STUDENT SELF PORTAL ENDPOINTS ──

@router.get("/student/me/profile", response_model=StudentProfileResponse, summary="Get Current Student Profile")
def get_current_student_profile(
    current_user: UserModel = Depends(require_student),
    db: Session = Depends(get_db)
):
    student = current_user.student
    if not student:
        from app.models.student import StudentModel
        student = db.query(StudentModel).filter(StudentModel.email == current_user.email).first()

    if not student:
        from app.core.exceptions import EntityNotFoundError
        raise EntityNotFoundError("Student profile for user", current_user.id)

    return {
        "id": student.id,
        "name": student.name,
        "roll_no": student.roll_no,
        "email": student.email,
        "department": student.department,
        "year": student.year,
        "division": student.division,
        "rfid_uid": student.rfid_uid,
        "face_enrolled": student.face_enrolled,
        "created_at": student.created_at.isoformat()
    }

@router.post("/student/me/face-enroll", response_model=FaceEnrollmentResponse, summary="Self-Enroll Biometrics")
async def self_enroll_face(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(require_student),
    db: Session = Depends(get_db)
):
    student = current_user.student
    if not student:
        from app.models.student import StudentModel
        student = db.query(StudentModel).filter(StudentModel.email == current_user.email).first()
    file_bytes = await file.read()
    return StudentService.enroll_face(db, student.id, file_bytes, file.filename)

@router.get("/student/{student_id}/stats", summary="Get Student Attendance Statistics")
def get_student_stats(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if current_user.role.upper() == "STUDENT":
        stu = current_user.student
        if not stu:
            from app.models.student import StudentModel
            stu = db.query(StudentModel).filter(StudentModel.email == current_user.email).first()
        if stu and stu.id != student_id and stu.user_id != student_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied. Students are restricted from viewing other students' attendance records."
            )
    return DashboardService.get_student_stats(db, student_id)

