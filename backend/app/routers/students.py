import json
import os
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.student import StudentModel
from app.models.face_embedding import FaceEmbeddingModel
from app.models.teacher import TeacherModel
from app.models.daily_checkin import DailyCheckinModel
from app.models.lecture_attendance import LectureAttendanceModel
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.schemas.face import FaceEnrollmentResponse
from app.services.face_embedding import get_face_embedder
from app.services.supabase_service import get_supabase_service
from app.core.security import get_current_teacher, get_current_teacher_or_admin, get_current_user, hash_password
from app.services.image_processor import (
    validate_image_file_security,
    decode_image_bytes,
    validate_image_quality_and_faces,
    crop_and_align_face,
    save_sanitized_student_image
)

router = APIRouter(prefix="/api/students", tags=["Students & Face Enrollment"])

@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED, summary="Create Student")
def create_student(
    student_in: StudentCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_teacher_or_admin)
):
    """
    Register a new student record (Teacher only).
    Checks for duplicate roll number, email, or RFID UID.
    """
    existing_roll = db.query(StudentModel).filter(StudentModel.roll_no == student_in.roll_no).first()
    if existing_roll:
        raise HTTPException(status_code=400, detail=f"Roll number '{student_in.roll_no}' is already registered.")

    rfid_val = student_in.rfid_uid.strip() if (student_in.rfid_uid and student_in.rfid_uid.strip()) else f"PENDING-{student_in.roll_no}"
    existing_rfid = db.query(StudentModel).filter(StudentModel.rfid_uid == rfid_val).first()
    if existing_rfid and not rfid_val.startswith("PENDING-"):
        raise HTTPException(status_code=400, detail=f"RFID UID '{rfid_val}' is already registered.")

    if student_in.email:
        existing_email = db.query(StudentModel).filter(StudentModel.email == student_in.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail=f"Email '{student_in.email}' is already registered.")

    password_hash = hash_password(student_in.password) if student_in.password else None

    student = StudentModel(
        name=student_in.name,
        roll_no=student_in.roll_no,
        department=student_in.department,
        year=student_in.year,
        division=student_in.division or "A",
        email=student_in.email,
        password_hash=password_hash,
        rfid_uid=rfid_val,
        face_enrolled=False,
        is_active=True
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    # Sync to Supabase
    supabase_service = get_supabase_service()
    if supabase_service.is_configured:
        supabase_service.sync_student({
            "id": student.id,
            "name": student.name,
            "roll_no": student.roll_no,
            "department": student.department,
            "year": student.year,
            "division": student.division,
            "email": student.email,
            "password_hash": password_hash,
            "rfid_uid": student.rfid_uid,
            "face_enrolled": False,
            "is_active": True
        })

    return student

@router.get("", response_model=List[StudentResponse], summary="List All Students")
def list_students(
    division_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_teacher_or_admin)
):
    """
    Retrieve list of enrolled students.
    Reads from Supabase students table when configured.
    """
    supabase_service = get_supabase_service()
    if supabase_service.is_configured:
        supa_students = supabase_service.get_students(division=division_id, search=q)
        if supa_students:
            return supa_students

    query = db.query(StudentModel)
    if division_id:
        query = query.filter(StudentModel.division == division_id)
    if q:
        query = query.filter(
            (StudentModel.name.ilike(f"%{q}%")) |
            (StudentModel.roll_no.ilike(f"%{q}%")) |
            (StudentModel.email.ilike(f"%{q}%"))
        )
    return query.order_by(StudentModel.id.desc()).all()

@router.get("/{student_id}", response_model=StudentResponse, summary="Get Student Details")
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_teacher_or_admin)
):
    """
    Fetch a single student by ID (Faculty or Admin).
    """
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID '{student_id}' not found.")
    return student

@router.put("/{student_id}", response_model=StudentResponse, summary="Update Student Information")
def update_student(
    student_id: int,
    student_in: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_teacher_or_admin)
):
    """
    Update student profile details (Faculty or Admin).
    """
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID '{student_id}' not found.")

    update_data = student_in.model_dump(exclude_unset=True)
    if "rfid_uid" in update_data and update_data["rfid_uid"] != student.rfid_uid:
        if current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers are not authorized to change or reassign student RFID cards. Use the authorized Admin RFID Card Assignment workflow."
            )

    if "password" in update_data:
        raw_pwd = update_data.pop("password")
        if raw_pwd:
            student.password_hash = hash_password(raw_pwd)

    for field, val in update_data.items():
        setattr(student, field, val)

    db.commit()
    db.refresh(student)

    supabase_service = get_supabase_service()
    if supabase_service.is_configured:
        supabase_service.sync_student({
            "id": student.id,
            "name": student.name,
            "roll_no": student.roll_no,
            "department": student.department,
            "year": student.year,
            "division": student.division,
            "email": student.email,
            "rfid_uid": student.rfid_uid,
            "is_active": student.is_active
        })

    return student

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Student and Face Enrollment")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_teacher_or_admin)
):
    """
    Delete a student record along with associated biometric assets (Faculty or Admin).
    """
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID '{student_id}' not found.")

    embeddings = db.query(FaceEmbeddingModel).filter(FaceEmbeddingModel.student_id == student_id).all()
    for emb in embeddings:
        if os.path.exists(emb.image_reference):
            try:
                os.remove(emb.image_reference)
            except Exception:
                pass

    db.query(DailyCheckinModel).filter(DailyCheckinModel.student_id == student_id).delete()
    db.query(LectureAttendanceModel).filter(LectureAttendanceModel.student_id == student_id).delete()

    db.delete(student)
    db.commit()

    supabase_service = get_supabase_service()
    if supabase_service.is_configured:
        try:
            supabase_service.client.table("students").delete().eq("id", student_id).execute()
        except Exception:
            pass

    return None

@router.patch("/{student_id}/deactivate", summary="Deactivate Student Account")
def deactivate_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_teacher_or_admin)
):
    """
    Deactivates a student account (Faculty or Admin).
    """
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID '{student_id}' not found.")
    student.is_active = False
    db.commit()
    db.refresh(student)

    supabase_service = get_supabase_service()
    if supabase_service.is_configured:
        supabase_service.sync_student({
            "id": student.id,
            "is_active": False
        })

    return {"status": "deactivated", "student_id": student.id, "is_active": False}

async def execute_face_enrollment(
    student_id: int,
    files: List[UploadFile],
    db: Session,
    caller_id: str,
    caller_role: str
) -> FaceEnrollmentResponse:
    """
    Executes biometric face enrollment pipeline:
    1. Validates format & file size.
    2. Runs InsightFace SCRFD-10G to require EXACTLY ONE usable face.
    3. Crops & aligns the detected face.
    4. Generates genuine ArcFace 512-d embedding.
    5. Persists image in private Supabase Storage 'student-enrollments'.
    6. Persists embedding vector in DB linked to student.
    7. Emits audit log event.
    """
    student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID '{student_id}' not found.")

    embedder = get_face_embedder()
    supabase_service = get_supabase_service()

    processed_count = 0
    successful_count = 0
    total_faces_detected = 0
    all_warnings: List[str] = []

    for upload_file in files:
        processed_count += 1
        file_bytes = await upload_file.read()

        # 1. Security & format validation
        try:
            validate_image_file_security(
                upload_file.filename or "face.jpg",
                upload_file.content_type or "image/jpeg",
                len(file_bytes)
            )
        except ValueError as err:
            raise HTTPException(status_code=400, detail=f"File '{upload_file.filename}': {str(err)}")

        # 2. Decode image
        try:
            img = decode_image_bytes(file_bytes)
        except ValueError as err:
            raise HTTPException(status_code=400, detail=f"File '{upload_file.filename}': {str(err)}")

        # 3. Quality & Face Count Validation (InsightFace SCRFD-10G)
        quality_res = validate_image_quality_and_faces(img)
        if not quality_res.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Image rejected: {quality_res.error_message}"
            )

        all_warnings.extend(quality_res.warnings)
        total_faces_detected += quality_res.faces_detected

        # 4. Extract Face Bounding Box & Alignment
        bbox = quality_res.bbox or (0, 0, img.shape[1], img.shape[0])
        face_crop = crop_and_align_face(img, bbox)

        # 5. Generate Embedding Vector (ArcFace-MobileFaceNet 512-d)
        embedding_vec = embedder.generate_embedding(face_crop)
        embedding_json = json.dumps(embedding_vec)

        # 6. Save image to Supabase Storage (private student-enrollments bucket)
        storage_info = supabase_service.upload_student_enrollment_image(
            student_id=student.id,
            file_bytes=file_bytes,
            filename=upload_file.filename or f"enrollment_{student.id}.jpg"
        )
        saved_filepath = storage_info.get("path") or save_sanitized_student_image(file_bytes, student.id, settings.STORAGE_DIR)

        # 7. Record Embedding in DB
        emb_record = FaceEmbeddingModel(
            student_id=student.id,
            embedding=embedding_json,
            image_reference=saved_filepath
        )
        db.add(emb_record)
        successful_count += 1

    if successful_count > 0:
        student.face_enrolled = True
        db.commit()
        db.refresh(student)

        if supabase_service.is_configured:
            try:
                supabase_service.client.table("students").update({"face_enrolled": True}).eq("id", student.id).execute()
            except Exception as e:
                logger.warning(f"Could not sync face_enrolled flag to Supabase: {e}")

        # 8. Record Audit Log
        supabase_service.log_audit_event(
            user_id=caller_id,
            role=caller_role,
            action="ENROLL_STUDENT_FACES",
            entity_type="STUDENT",
            entity_id=str(student.id),
            details={"images_enrolled": successful_count, "total_faces_detected": total_faces_detected},
            db_session=db
        )

    return FaceEnrollmentResponse(
        student_id=student.id,
        images_processed=processed_count,
        faces_detected=total_faces_detected,
        successful_embeddings=successful_count,
        status="enrolled" if student.face_enrolled else "failed",
        quality_warnings=list(set(all_warnings))
    )

@router.post("/me/face-enroll", response_model=FaceEnrollmentResponse, summary="Student Self Face Enrollment Alias")
async def self_enroll_student_faces(
    files: Optional[List[UploadFile]] = File(None, description="One or more photographs of student's face"),
    file: Optional[UploadFile] = File(None, description="Single photograph captured from camera"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    role = str(current_user.get("role", "")).upper()
    user_obj = current_user.get("user")
    if role != "STUDENT" or not user_obj:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Only authenticated students may self-enroll."
        )
    upload_list: List[UploadFile] = []
    if file:
        upload_list.append(file)
    if files:
        upload_list.extend(files)
    if not upload_list:
        raise HTTPException(status_code=400, detail="No photograph file provided for face enrollment.")
    return await execute_face_enrollment(
        student_id=user_obj.id,
        files=upload_list,
        db=db,
        caller_id=str(user_obj.id),
        caller_role="STUDENT"
    )

@router.post("/{student_id}/face-enroll", response_model=FaceEnrollmentResponse, summary="Enroll Student Face Images")
async def enroll_student_faces(
    student_id: int,
    files: Optional[List[UploadFile]] = File(None, description="One or more photographs of student's face"),
    file: Optional[UploadFile] = File(None, description="Single photograph captured from camera"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Enroll a student's face biometrics.
    - Teachers and Admins can enroll any student.
    - Enrolled students can enroll their own face profile.
    - Unauthorized students cannot enroll or replace other students' face profiles.
    """
    role = str(current_user.get("role", "")).upper()
    user_obj = current_user.get("user")
    caller_id = str(getattr(user_obj, "id", current_user.get("user_id", "unknown")))

    if role == "STUDENT":
        if not user_obj or user_obj.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You may only enroll biometric face data for your own student account."
            )
    elif role not in ["TEACHER", "ADMIN", "SERVICE_ROLE"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Insufficient privileges for biometric face enrollment."
        )

    upload_list: List[UploadFile] = []
    if file:
        upload_list.append(file)
    if files:
        upload_list.extend(files)

    if not upload_list:
        raise HTTPException(status_code=400, detail="No photograph file provided for face enrollment.")

    return await execute_face_enrollment(
        student_id=student_id,
        files=upload_list,
        db=db,
        caller_id=caller_id,
        caller_role=role
    )
