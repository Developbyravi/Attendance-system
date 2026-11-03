import json
import time
from datetime import datetime, timezone, date
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.student import StudentModel
from app.models.teacher import TeacherModel
from app.models.face_embedding import FaceEmbeddingModel
from app.models.daily_checkin import DailyCheckinModel
from app.models.lecture_session import LectureSessionModel
from app.models.lecture_attendance import LectureAttendanceModel

from app.schemas.lecture import (
    LectureCreate,
    LectureResponse,
    LectureAttendanceItem,
    LectureVerificationSummary,
    DetectedFaceBox,
    FlagResolutionRequest,
    StudentAttendanceUpdate
)
import cv2
from app.services.face_detector import get_face_detector
from app.services.face_recognition import get_face_recognition_service
from app.services.image_processor import (
    validate_image_file_security,
    decode_image_bytes,
    crop_and_align_face,
    extract_all_face_crops_with_conf,
    draw_detection_overlay
)
from app.services.supabase_service import get_supabase_service
from app.services.verification_engine import VerificationEngine
from app.core.security import get_current_teacher, get_current_user

router = APIRouter(prefix="/api/lectures", tags=["Per-Lecture Attendance"])

@router.post("", response_model=LectureResponse, status_code=status.HTTP_201_CREATED, summary="Create Lecture Session")
def create_lecture(
    req: LectureCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Teacher or Admin creates a new per-lecture attendance session.
    """
    role = str(current_user.get("role", "")).upper()
    if role not in ["TEACHER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Teacher or Administrator privileges required"
        )

    if role == "TEACHER":
        teacher_id = current_user["user"].id
    else:
        first_tch = db.query(TeacherModel).first()
        teacher_id = first_tch.id if first_tch else 1

    # Resolve division: either passed as division or division_id
    raw_div = req.division_id if req.division_id is not None else req.division
    if raw_div is None:
        raw_div = "A"
    division_str = str(raw_div).strip()
    div_model = None
    from app.models.division import DivisionModel
    if division_str.isdigit():
        try:
            div_model = db.query(DivisionModel).filter(DivisionModel.id == int(division_str)).first()
            if div_model:
                division_str = div_model.name
        except Exception as e:
            logger.warning(f"Could not resolve division id {division_str}: {e}")
    else:
        try:
            div_model = db.query(DivisionModel).filter(DivisionModel.name == division_str).first()
        except Exception:
            pass

    # Resolve date
    lecture_date = date.today()
    raw_date = req.date or req.lecture_date
    if raw_date:
        if isinstance(raw_date, date):
            lecture_date = raw_date
        elif isinstance(raw_date, str):
            try:
                lecture_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except Exception:
                lecture_date = date.today()

    lecture = LectureSessionModel(
        teacher_id=teacher_id,
        subject=req.subject,
        division=division_str,
        date=lecture_date,
        status="ACTIVE"
    )
    db.add(lecture)
    db.commit()
    db.refresh(lecture)
    setattr(lecture, 'division_name', f"Division {division_str}")
    setattr(lecture, 'division_id', div_model.id if div_model else None)
    return lecture

@router.get("", response_model=List[LectureResponse], summary="List Teacher's Lectures")
def list_lectures(
    teacher_id: Optional[Any] = Query(None),
    date_val: Optional[Any] = Query(None, alias="date"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retrieves lecture sessions created by the authenticated teacher or all lectures for Admin.
    """
    role = str(current_user.get("role", "")).upper()
    if role not in ["TEACHER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Teacher or Administrator privileges required"
        )

    query = db.query(LectureSessionModel)
    if role == "TEACHER":
        query = query.filter(LectureSessionModel.teacher_id == current_user["user"].id)
    elif teacher_id and str(teacher_id).isdigit():
        query = query.filter(LectureSessionModel.teacher_id == int(teacher_id))

    if date_val:
        parsed_d = None
        if isinstance(date_val, date):
            parsed_d = date_val
        elif isinstance(date_val, str):
            try:
                parsed_d = datetime.strptime(date_val, "%Y-%m-%d").date()
            except Exception:
                pass
        if parsed_d:
            query = query.filter(LectureSessionModel.date == parsed_d)

    lectures = query.order_by(LectureSessionModel.created_at.desc()).all()
    from app.models.division import DivisionModel
    div_map = {d.name: d.id for d in db.query(DivisionModel).all()}
    for lec in lectures:
        setattr(lec, 'division_name', f"Division {lec.division}")
        setattr(lec, 'division_id', div_map.get(lec.division))
    return lectures

@router.get("/{lecture_id}", summary="Get Lecture Session Details")
def get_lecture(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get detailed lecture info and student attendance roster (Teacher or Admin authorized).
    """
    role = str(current_user.get("role", "")).upper()
    if role not in ["TEACHER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Teacher or Administrator privileges required"
        )

    query = db.query(LectureSessionModel).filter(LectureSessionModel.id == lecture_id)
    if role == "TEACHER":
        query = query.filter(LectureSessionModel.teacher_id == current_user["user"].id)

    lecture = query.first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture session not found.")

    attendances = db.query(LectureAttendanceModel).filter(
        LectureAttendanceModel.lecture_session_id == lecture.id
    ).all()

    att_items = []
    for a in attendances:
        st = a.student
        att_items.append({
            "id": a.id,
            "lecture_session_id": a.lecture_session_id,
            "student_id": a.student_id,
            "student_name": st.name if st else "Unknown",
            "roll_no": st.roll_no if st else "",
            "department": st.department if st else "",
            "division": st.division if st else "",
            "status": a.status,
            "verification_source": a.verification_source,
            "ai_confidence": a.ai_confidence,
            "rfid_checked_in": a.rfid_checked_in,
            "ai_detected": a.ai_detected,
            "teacher_action": a.teacher_action,
            "finalized": a.finalized
        })

    present_cnt = sum(1 for a in attendances if a.status == "PRESENT")
    absent_cnt = sum(1 for a in attendances if a.status == "ABSENT")
    flagged_cnt = sum(1 for a in attendances if a.status == "FLAGGED")
    pending_cnt = sum(1 for a in attendances if a.status == "PENDING")

    from app.models.division import DivisionModel
    div_rec = db.query(DivisionModel).filter(DivisionModel.name == lecture.division).first()

    return {
        "id": lecture.id,
        "teacher_id": lecture.teacher_id,
        "subject": lecture.subject,
        "title": f"{lecture.subject} (Division {lecture.division})",
        "division": lecture.division,
        "division_name": f"Division {lecture.division}",
        "division_id": div_rec.id if div_rec else None,
        "date": lecture.date.isoformat(),
        "lecture_date": lecture.date.isoformat(),
        "start_time": lecture.start_time.strftime("%H:%M") if lecture.start_time else "09:00",
        "end_time": lecture.end_time.strftime("%H:%M") if lecture.end_time else None,
        "status": lecture.status.lower() if lecture.status else "scheduled",
        "raw_status": lecture.status,
        "created_at": lecture.created_at.isoformat(),
        "total_enrolled": len(attendances),
        "present_count": present_cnt,
        "absent_count": absent_cnt,
        "flagged_count": flagged_cnt,
        "pending_count": pending_cnt,
        "classroom_photo_url": lecture.classroom_photo_url,
        "overlay_image_url": lecture.overlay_image_url,
        "attendances": att_items
    }

@router.post("/{lecture_id}/photo", response_model=LectureVerificationSummary, summary="Process Classroom Photo & Run Division Verification")
@router.post("/{lecture_id}/verify-photo", response_model=LectureVerificationSummary, summary="Process Classroom Photo & Run Division Verification (Alias)")
async def verify_classroom_photo_for_lecture(
    lecture_id: int,
    file: Optional[UploadFile] = File(None),
    photo: Optional[UploadFile] = File(None),
    threshold: float = Query(default=settings.FACE_RECOGNITION_THRESHOLD, ge=0.0, le=1.0),
    auto_mark_absent: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: TeacherModel = Depends(get_current_teacher)
):
    """
    Uploads classroom photograph for a specific lecture.
    1. AI detects faces and matches against enrolled embeddings.
    2. Filters students strictly by lecture's division.
    3. Cross-verifies against today's Daily RFID check-ins.
    4. Creates/updates LectureAttendance records for ALL division students.
    """
    lecture = db.query(LectureSessionModel).filter(
        LectureSessionModel.id == lecture_id,
        LectureSessionModel.teacher_id == current_teacher.id
    ).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture session not found.")

    if lecture.status == "FINALIZED":
        raise HTTPException(status_code=400, detail="Cannot upload photo to a FINALIZED lecture session.")

    target_file = file or photo
    if not target_file:
        raise HTTPException(status_code=400, detail="Classroom photograph file is required.")

    file_bytes = await target_file.read()
    validate_image_file_security(target_file.filename or "classroom.jpg", target_file.content_type or "image/jpeg", len(file_bytes))
    img = decode_image_bytes(file_bytes)

    # 1. Upload classroom image to Supabase Storage (with local fallback)
    supabase_service = get_supabase_service()
    storage_info = supabase_service.upload_classroom_image(
        lecture_id=lecture.id,
        file_bytes=file_bytes,
        filename=target_file.filename or "classroom.jpg"
    )

    rec_service = get_face_recognition_service()
    # 2. Run face detector (InsightFace SCRFD-10G with 5-point landmarks & alignment, supports test mocks)
    detector = get_face_detector()
    if hasattr(detector, 'detect_faces_with_landmarks'):
        detections = detector.detect_faces_with_landmarks(img)
        detected_face_items = []
        for item in detections:
            bbox = item["bbox"]
            conf = item["conf"]
            landmarks = item.get("landmarks")
            crop = crop_and_align_face(img, bbox, landmarks=landmarks)
            if crop is not None and crop.size > 0:
                detected_face_items.append({
                    "bbox": bbox,
                    "conf": conf,
                    "landmarks": landmarks,
                    "face_crop": crop
                })
    elif hasattr(detector, 'detect_faces_with_conf'):
        detections = detector.detect_faces_with_conf(img)
        detected_face_items = []
        for bbox, conf in detections:
            crop = crop_and_align_face(img, bbox)
            if crop is not None and crop.size > 0:
                detected_face_items.append({
                    "bbox": bbox,
                    "conf": conf,
                    "landmarks": None,
                    "face_crop": crop
                })
    else:
        boxes = detector.detect_faces(img)
        detected_face_items = []
        for bbox in boxes:
            crop = crop_and_align_face(img, bbox)
            if crop is not None and crop.size > 0:
                detected_face_items.append({
                    "bbox": bbox,
                    "conf": 1.0,
                    "landmarks": None,
                    "face_crop": crop
                })

    # 3. Fetch active students in lecture's division ONLY (resolving numeric division ID if present)
    target_div = lecture.division
    div_rec = None
    from app.models.division import DivisionModel
    if target_div and str(target_div).isdigit():
        div_rec = db.query(DivisionModel).filter(DivisionModel.id == int(target_div)).first()
        if div_rec:
            target_div = div_rec.name
            lecture.division = target_div
            db.commit()
    elif target_div:
        div_rec = db.query(DivisionModel).filter(DivisionModel.name == target_div).first()

    # Teacher authorization check
    if current_teacher and getattr(current_teacher, 'assigned_divisions', None):
        try:
            assigned = json.loads(current_teacher.assigned_divisions)
        except Exception:
            assigned = [d.strip() for d in str(current_teacher.assigned_divisions).split(",") if d.strip()]
        if assigned:
            div_id_str = str(div_rec.id) if div_rec else ""
            if target_div not in assigned and lecture.division not in assigned and div_id_str not in assigned:
                logger.warning(f"Teacher {current_teacher.id} assigned divisions {assigned} does not explicitly include {target_div}")

    from sqlalchemy import or_, and_
    upper_div = str(target_div or "").strip().upper()
    if "AIML" in upper_div or "AI" in upper_div:
        letter = "B" if "B" in upper_div else "A"
        student_query = db.query(StudentModel).filter(
            or_(
                StudentModel.division == target_div,
                StudentModel.division == lecture.division,
                and_(
                    StudentModel.division == letter,
                    or_(
                        StudentModel.department.ilike("%AI%"),
                        StudentModel.department.ilike("%Machine%")
                    )
                )
            ),
            StudentModel.is_active == True
        )
    else:
        student_query = db.query(StudentModel).filter(
            or_(
                StudentModel.division == target_div,
                StudentModel.division == lecture.division
            ),
            StudentModel.is_active == True
        )

    division_students_db = student_query.all()
    division_student_ids = {s.id for s in division_students_db}
    division_student_dicts = [
        {"id": s.id, "name": s.name, "roll_no": s.roll_no, "department": s.department, "division": s.division}
        for s in division_students_db
    ]

    # 4. Fetch enrolled embeddings for division students
    enrolled_map: Dict[int, Dict[str, Any]] = {}
    for s in division_students_db:
        emb_records = db.query(FaceEmbeddingModel).filter(FaceEmbeddingModel.student_id == s.id).all()
        if emb_records:
            parsed = []
            for rec in emb_records:
                try:
                    parsed.append(json.loads(rec.embedding))
                except Exception:
                    pass
            if parsed:
                if not s.face_enrolled:
                    s.face_enrolled = True
                    db.commit()
                enrolled_map[s.id] = {
                    "student": {"id": s.id, "name": s.name, "roll_no": s.roll_no, "department": s.department, "division": s.division},
                    "embeddings": parsed
                }

    # 5. Process detections: match embeddings, check ambiguity, deduplicate repeated detections
    detection_results = rec_service.process_classroom_detections(
        detected_faces=detected_face_items,
        enrolled_student_map=enrolled_map,
        threshold=threshold
    )

    ai_recognized_map: Dict[int, float] = {
        sid: item.get("similarity", item.get("confidence", 0.0))
        for sid, item in detection_results["recognized"].items()
    }

    # 6. Fetch today's DailyCheckins for division students
    daily_checkins = db.query(DailyCheckinModel).filter(
        DailyCheckinModel.date == lecture.date,
        DailyCheckinModel.student_id.in_(division_student_ids) if division_student_ids else False
    ).all()
    daily_checked_in_ids = {c.student_id for c in daily_checkins}

    # Handle ambiguous detections: resolve via daily RFID check-in or flag candidate(s) for teacher review
    for item in detection_results.get("ambiguous", []):
        details = item.get("ambiguity_details") or {}
        candidates = details.get("candidates") or []
        if not candidates:
            c1 = item.get("student")
            c2 = details.get("secondary_candidate")
            if c1:
                candidates.append({"student": c1, "similarity": item.get("similarity", 0.0)})
            if c2:
                candidates.append({"student": c2, "similarity": details.get("secondary_similarity", 0.0)})

        # Exclude candidates already recognized and assigned to other distinct faces in this photograph
        unassigned_candidates = [
            c for c in candidates
            if c.get("student", {}).get("id") and c.get("student", {}).get("id") not in ai_recognized_map
        ]

        if len(unassigned_candidates) == 1:
            best = unassigned_candidates[0]
            sid = best["student"]["id"]
            sim = float(best.get("similarity", 0.0))
            ai_recognized_map[sid] = max(ai_recognized_map.get(sid, 0.0), sim)
            item["resolved_student"] = best["student"]
            item["resolved_similarity"] = sim
        elif len(unassigned_candidates) > 1:
            # Check if exactly one candidate among unassigned candidates has daily RFID check-in -> resolve ambiguity!
            rfid_matched = [c for c in unassigned_candidates if c.get("student", {}).get("id") in daily_checked_in_ids]
            if len(rfid_matched) == 1:
                best = rfid_matched[0]
                sid = best["student"]["id"]
                sim = float(best.get("similarity", 0.0))
                ai_recognized_map[sid] = max(ai_recognized_map.get(sid, 0.0), sim)
                item["resolved_student"] = best["student"]
                item["resolved_similarity"] = sim
            else:
                # Ambiguity remains unresolvable via RFID (0 or multiple checked in)
                # Keep candidate list clean for teacher review
                item["ambiguity_details"]["candidates"] = unassigned_candidates

    # Truly unknown faces (similarity < threshold)
    unknown_faces_list = detection_results.get("unknown", [])

    # Determine whether to auto mark undetected students absent based on configured workflow
    should_auto_mark_absent = auto_mark_absent if auto_mark_absent is not None else settings.AUTO_MARK_ABSENT_ON_PHOTO

    # 7. Run VerificationEngine matrix
    matrix = VerificationEngine.compute_lecture_verification_matrix(
        division_students=division_student_dicts,
        daily_checked_in_student_ids=daily_checked_in_ids,
        ai_recognized_map=ai_recognized_map,
        unknown_faces_list=unknown_faces_list,
        auto_mark_absent=should_auto_mark_absent
    )

    # 8. Save attendance entries for ALL division students
    db.query(LectureAttendanceModel).filter(
        LectureAttendanceModel.lecture_session_id == lecture.id
    ).delete()
    db.commit()

    saved_items = []
    for item in matrix["results"]:
        att = LectureAttendanceModel(
            lecture_session_id=lecture.id,
            student_id=item["student_id"],
            status=item["status"],
            verification_source=item["verification_source"],
            ai_confidence=item["ai_confidence"],
            rfid_checked_in=item["rfid_checked_in"],
            ai_detected=item["ai_detected"],
            finalized=False
        )
        db.add(att)
        db.flush()

        saved_items.append(LectureAttendanceItem(
            id=att.id,
            lecture_session_id=lecture.id,
            student_id=item["student_id"],
            student_name=item["student_name"],
            roll_no=item["roll_no"],
            department=item["department"],
            division=item["division"],
            status=item["status"],
            verification_source=item["verification_source"],
            ai_confidence=item["ai_confidence"],
            rfid_checked_in=item["rfid_checked_in"],
            ai_detected=item["ai_detected"],
            teacher_action=None,
            finalized=False
        ))

    # Build detailed detected_boxes for visual inspection
    detected_boxes: List[DetectedFaceBox] = []

    # 1. Recognized
    for sid, rec in detection_results.get("recognized", {}).items():
        st = rec.get("student") or {}
        bbox = rec.get("bbox") or [0, 0, 0, 0]
        detected_boxes.append(DetectedFaceBox(
            bbox=[int(v) for v in bbox],
            detector_confidence=round(float(rec.get("detector_confidence", 1.0)), 3),
            similarity=round(float(rec.get("similarity", 0.0)), 3),
            match_status="recognized",
            student_id=st.get("id"),
            student_name=st.get("name"),
            roll_no=st.get("roll_no")
        ))

    # 2. Ambiguous / Resolved
    for rec in detection_results.get("ambiguous", []):
        resolved_st = rec.get("resolved_student")
        if resolved_st:
            bbox = rec.get("bbox") or [0, 0, 0, 0]
            detected_boxes.append(DetectedFaceBox(
                bbox=[int(v) for v in bbox],
                detector_confidence=round(float(rec.get("detector_confidence", 1.0)), 3),
                similarity=round(float(rec.get("resolved_similarity", rec.get("similarity", 0.0))), 3),
                match_status="recognized",
                student_id=resolved_st.get("id"),
                student_name=resolved_st.get("name"),
                roll_no=resolved_st.get("roll_no")
            ))
        else:
            st = rec.get("student") or {}
            bbox = rec.get("bbox") or [0, 0, 0, 0]
            detected_boxes.append(DetectedFaceBox(
                bbox=[int(v) for v in bbox],
                detector_confidence=round(float(rec.get("detector_confidence", 1.0)), 3),
                similarity=round(float(rec.get("similarity", 0.0)), 3),
                match_status="ambiguous",
                student_id=st.get("id"),
                student_name=st.get("name"),
                roll_no=st.get("roll_no")
            ))

    # 3. Unknown
    for rec in detection_results.get("unknown", []):
        bbox = rec.get("bbox") or [0, 0, 0, 0]
        detected_boxes.append(DetectedFaceBox(
            bbox=[int(v) for v in bbox],
            detector_confidence=round(float(rec.get("detector_confidence", 1.0)), 3),
            similarity=None,
            match_status="unknown",
            student_id=None,
            student_name=None,
            roll_no=None
        ))

    # 4. Duplicates
    for rec in detection_results.get("duplicates", []):
        st = rec.get("student") or {}
        bbox = rec.get("bbox") or [0, 0, 0, 0]
        detected_boxes.append(DetectedFaceBox(
            bbox=[int(v) for v in bbox],
            detector_confidence=round(float(rec.get("detector_confidence", 1.0)), 3),
            similarity=round(float(rec.get("similarity", 0.0)), 3),
            match_status="duplicate",
            student_id=st.get("id"),
            student_name=st.get("name"),
            roll_no=st.get("roll_no")
        ))

    # Generate visually distinct classroom detection overlay
    overlay_url = None
    try:
        box_dicts = [b.model_dump() for b in detected_boxes]
        annotated_img = draw_detection_overlay(img, box_dicts)
        success, encoded_jpg = cv2.imencode(".jpg", annotated_img, [cv2.IMWRITE_JPEG_QUALITY, 88])
        if success:
            annotated_bytes = encoded_jpg.tobytes()
            overlay_storage = supabase_service.upload_classroom_image(
                lecture_id=lecture.id,
                file_bytes=annotated_bytes,
                filename=f"annotated_lecture_{lecture.id}.jpg"
            )
            overlay_url = overlay_storage.get("url")
    except Exception:
        overlay_url = None

    lecture.classroom_photo_url = storage_info.get("url")
    lecture.overlay_image_url = overlay_url
    db.commit()

    # 9. Audit event
    supabase_service.log_audit_event(
        user_id=str(current_teacher.id),
        role="TEACHER",
        action="PROCESS_CLASSROOM_PHOTO",
        entity_type="LECTURE_SESSION",
        entity_id=str(lecture.id),
        details={
            "detected_faces": len(detected_face_items),
            "verified_present": matrix["verified_present"],
            "storage_path": storage_info.get("path")
        },
        db_session=db
    )

    return LectureVerificationSummary(
        lecture_id=lecture.id,
        subject=lecture.subject,
        division=lecture.division,
        date=lecture.date.isoformat(),
        daily_rfid_checked_in=matrix["daily_rfid_checked_in"],
        ai_detected_count=matrix["ai_detected_count"],
        verified_present=matrix["verified_present"],
        rfid_only=matrix["rfid_only"],
        ai_only=matrix["ai_only"],
        absent=matrix["absent"],
        pending=matrix.get("pending", 0),
        unknown_faces=matrix["unknown_faces"],
        attendances=saved_items,
        photo_url=storage_info.get("url"),
        overlay_image_url=overlay_url,
        detected_faces=len(detected_face_items),
        detected_boxes=detected_boxes,
        detector="InsightFace SCRFD-10G"
    )

@router.post("/{lecture_id}/resolve-flag", summary="Teacher Flag Resolution")
def resolve_flag(
    lecture_id: int,
    req: FlagResolutionRequest,
    db: Session = Depends(get_db),
    current_teacher: TeacherModel = Depends(get_current_teacher)
):
    """
    Teacher resolves an RFID_ONLY or AI_ONLY flag for a student.
    Actions: CONFIRM_PRESENT | MARK_ABSENT
    """
    lecture = db.query(LectureSessionModel).filter(
        LectureSessionModel.id == lecture_id,
        LectureSessionModel.teacher_id == current_teacher.id
    ).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture session not found.")

    if lecture.status == "FINALIZED":
        raise HTTPException(status_code=400, detail="Cannot resolve flags for a FINALIZED lecture session.")

    att = db.query(LectureAttendanceModel).filter(
        LectureAttendanceModel.lecture_session_id == lecture.id,
        LectureAttendanceModel.student_id == req.student_id
    ).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attendance record for this student not found.")

    if req.action not in ["CONFIRM_PRESENT", "MARK_ABSENT"]:
        raise HTTPException(status_code=400, detail="Invalid action. Must be CONFIRM_PRESENT or MARK_ABSENT.")

    if req.action == "CONFIRM_PRESENT":
        att.status = "PRESENT"
        att.verification_source = "TEACHER_CONFIRMED"
        att.teacher_action = "CONFIRMED_PRESENT"
    elif req.action == "MARK_ABSENT":
        att.status = "ABSENT"
        att.verification_source = "TEACHER_MARKED_ABSENT"
        att.teacher_action = "MARKED_ABSENT"

    db.commit()
    db.refresh(att)
    st = att.student

    # Audit event for flag resolution
    supabase_service = get_supabase_service()
    supabase_service.log_audit_event(
        user_id=str(current_teacher.id),
        role="TEACHER",
        action="RESOLVE_FLAG",
        entity_type="LECTURE_ATTENDANCE",
        entity_id=str(att.id),
        details={"student_id": req.student_id, "action": req.action, "new_status": att.status},
        db_session=db
    )

    return LectureAttendanceItem(
        id=att.id,
        lecture_session_id=att.lecture_session_id,
        student_id=att.student_id,
        student_name=st.name if st else "Unknown",
        roll_no=st.roll_no if st else "",
        department=st.department if st else "",
        division=st.division if st else "",
        status=att.status,
        verification_source=att.verification_source,
        ai_confidence=att.ai_confidence,
        rfid_checked_in=att.rfid_checked_in,
        ai_detected=att.ai_detected,
        teacher_action=att.teacher_action,
        finalized=att.finalized
    )

@router.post("/{lecture_id}/finalize", summary="Finalize Lecture Attendance Session")
def finalize_lecture(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_teacher: TeacherModel = Depends(get_current_teacher)
):
    """
    Finalizes the lecture session, locking all attendance records as immutable.
    """
    lecture = db.query(LectureSessionModel).filter(
        LectureSessionModel.id == lecture_id,
        LectureSessionModel.teacher_id == current_teacher.id
    ).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture session not found.")

    if lecture.status == "FINALIZED":
        raise HTTPException(status_code=400, detail="Lecture session is already FINALIZED.")

    attendances = db.query(LectureAttendanceModel).filter(
        LectureAttendanceModel.lecture_session_id == lecture.id
    ).all()

    for att in attendances:
        if att.status == "PENDING":
            att.status = "ABSENT"
            att.verification_source = "FINALIZED_ABSENT"
        att.finalized = True

    lecture.status = "FINALIZED"
    lecture.end_time = datetime.now(timezone.utc)
    db.commit()

    # Audit event for lecture finalization
    supabase_service = get_supabase_service()
    supabase_service.log_audit_event(
        user_id=str(current_teacher.id),
        role="TEACHER",
        action="FINALIZE_LECTURE",
        entity_type="LECTURE_SESSION",
        entity_id=str(lecture.id),
        details={"total_records": len(attendances)},
        db_session=db
    )

    return {"status": "FINALIZED", "lecture_id": lecture.id, "total_records": len(attendances)}

@router.get("/{lecture_id}/review", summary="Get Lecture Attendance Review Roster")
def get_lecture_review_roster(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_teacher: TeacherModel = Depends(get_current_teacher)
):
    """
    Returns the attendance review roster formatted for the teacher review dashboard.
    """
    lecture = db.query(LectureSessionModel).filter(
        LectureSessionModel.id == lecture_id,
        LectureSessionModel.teacher_id == current_teacher.id
    ).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture session not found.")

    attendances = db.query(LectureAttendanceModel).filter(
        LectureAttendanceModel.lecture_session_id == lecture.id
    ).all()

    roster = []
    for a in attendances:
        st = a.student
        roster.append({
            "id": a.id,
            "student_id": a.student_id,
            "student_name": st.name if st else "Unknown",
            "roll_number": st.roll_no if st else "",
            "daily_rfid_status": "CHECKED_IN" if a.rfid_checked_in else "NOT_CHECKED_IN",
            "daily_check_in_time": None,
            "ai_verification_status": "VERIFIED" if a.ai_detected else ("NOT_DETECTED" if not a.rfid_checked_in else "FLAGGED"),
            "confidence_score": a.ai_confidence,
            "attendance_status": a.status,
            "verification_source": a.verification_source,
            "notes": a.teacher_action
        })
    return roster

@router.patch("/{lecture_id}/students/{student_id}", summary="Update Student Attendance in Lecture")
def update_student_attendance(
    lecture_id: int,
    student_id: int,
    req: StudentAttendanceUpdate,
    db: Session = Depends(get_db),
    current_teacher: TeacherModel = Depends(get_current_teacher)
):
    """
    Teacher manually sets/overrides student attendance status during review.
    Enforces strict immutability if lecture is already FINALIZED.
    """
    lecture = db.query(LectureSessionModel).filter(
        LectureSessionModel.id == lecture_id,
        LectureSessionModel.teacher_id == current_teacher.id
    ).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture session not found.")

    if lecture.status == "FINALIZED":
        raise HTTPException(status_code=400, detail="Cannot alter attendance of a FINALIZED lecture session.")

    att = db.query(LectureAttendanceModel).filter(
        LectureAttendanceModel.lecture_session_id == lecture.id,
        LectureAttendanceModel.student_id == student_id
    ).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attendance record for student not found in this lecture.")

    valid_statuses = ["PRESENT", "ABSENT", "FLAGGED", "PENDING"]
    if req.status.upper() not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status '{req.status}'. Must be one of {valid_statuses}.")

    att.status = req.status.upper()
    att.verification_source = "TEACHER_MANUAL"
    att.teacher_action = req.reason or f"MANUALLY_MARKED_{req.status.upper()}"
    db.commit()
    db.refresh(att)

    # Audit event
    get_supabase_service().log_audit_event(
        user_id=str(current_teacher.id),
        role="TEACHER",
        action="OVERRIDE_ATTENDANCE",
        entity_type="LECTURE_ATTENDANCE",
        entity_id=str(att.id),
        details={"student_id": student_id, "new_status": att.status, "reason": req.reason},
        db_session=db
    )

    return {"status": "success", "student_id": student_id, "attendance_status": att.status}
