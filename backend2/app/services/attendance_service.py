import cv2
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.lecture import LectureSessionModel
from app.models.student import StudentModel
from app.models.daily_checkin import DailyCheckinModel
from app.models.attendance import LectureAttendanceModel, AttendanceAuditLogModel
from app.models.face_embedding import FaceEmbeddingModel
from app.ai.recognizer import FaceRecognitionPipeline
from app.utils.image_utils import draw_detection_overlay
from app.services.storage_service import get_storage_service
from app.config import settings
from app.core.exceptions import EntityNotFoundError, SessionFinalizedError, SmartAttendException

logger = logging.getLogger(__name__)

class AttendanceService:
    @staticmethod
    def process_lecture_photo(
        db: Session,
        lecture_id: int,
        image_bytes: bytes,
        filename: Optional[str] = None,
        threshold: float = 0.70,
        auto_mark_absent: bool = False
    ) -> Dict[str, Any]:
        """
        Executes complete Per-Lecture AI + Daily RFID Cross-Verification Attendance Workflow.
        """
        lecture = db.query(LectureSessionModel).filter(LectureSessionModel.id == lecture_id).first()
        if not lecture:
            raise EntityNotFoundError("Lecture Session", lecture_id)

        if lecture.status == "FINALIZED":
            raise SessionFinalizedError(lecture.id)

        # 1. Save raw classroom photo
        storage_service = get_storage_service()
        photo_info = storage_service.save_classroom_image(lecture.id, image_bytes, filename)
        raw_photo_url = photo_info["url"]

        # 2. Decode image for CV inference
        from app.ai.preprocessing import decode_image_bytes
        img = decode_image_bytes(image_bytes)

        # 3. Fetch active division students strictly belonging to this lecture
        target_div = lecture.division
        div_students = db.query(StudentModel).filter(
            or_(
                StudentModel.division == target_div,
                StudentModel.division == f"Div {target_div}",
                StudentModel.division == f"Division {target_div}"
            ),
            StudentModel.is_active == True
        ).all()

        division_student_map = {s.id: s for s in div_students}

        # 4. Fetch enrolled face embeddings for division students
        enrolled_map: Dict[int, Dict[str, Any]] = {}
        for s in div_students:
            embs = db.query(FaceEmbeddingModel).filter(FaceEmbeddingModel.student_id == s.id).all()
            if embs:
                parsed_list = []
                for e in embs:
                    emb_vec = e.embedding_list
                    if emb_vec and len(emb_vec) == 512:
                        parsed_list.append(emb_vec)
                if parsed_list:
                    enrolled_map[s.id] = {
                        "student": {
                            "id": s.id,
                            "name": s.name,
                            "roll_no": s.roll_no,
                            "division": s.division,
                            "department": s.department
                        },
                        "embeddings": parsed_list
                    }

        # 5. Fetch today's Daily RFID check-ins for division students
        daily_checkins = db.query(DailyCheckinModel).filter(
            DailyCheckinModel.date == lecture.date,
            DailyCheckinModel.student_id.in_(list(division_student_map.keys())) if division_student_map else False
        ).all()
        daily_checked_in_ids = {c.student_id for c in daily_checkins}

        # 6. Run AI recognition pipeline (SCRFD-10G + ArcFace)
        ai_pipeline = FaceRecognitionPipeline.get_instance()
        detection_res = ai_pipeline.identify_classroom_faces(img, enrolled_map, threshold=threshold)

        recognized_map: Dict[int, Dict[str, Any]] = detection_res.get("recognized", {})
        ambiguous_list: List[Dict[str, Any]] = detection_res.get("ambiguous", [])
        unknown_list: List[Dict[str, Any]] = detection_res.get("unknown", [])
        duplicate_list: List[Dict[str, Any]] = detection_res.get("duplicates", [])

        # 7. Disambiguate ambiguous detections using morning RFID check-in if possible
        ai_verified_student_ids: Dict[int, float] = {
            sid: rec.get("similarity", 0.0) for sid, rec in recognized_map.items()
        }

        ambiguous_flagged_students: Dict[int, Dict[str, Any]] = {}

        for amb in ambiguous_list:
            details = amb.get("ambiguity_details", {})
            candidates = details.get("candidates", [])
            unassigned_cands = [
                c for c in candidates
                if c.get("student", {}).get("id") not in ai_verified_student_ids
            ]

            # Check if exactly one candidate has daily RFID check-in
            rfid_candidates = [
                c for c in unassigned_cands
                if c.get("student", {}).get("id") in daily_checked_in_ids
            ]

            if len(rfid_candidates) == 1:
                # Disambiguated by physical RFID presence!
                best = rfid_candidates[0]
                sid = best["student"]["id"]
                sim = float(best.get("similarity", 0.0))
                ai_verified_student_ids[sid] = sim
                amb["match_status"] = "recognized"
                amb["student"] = best["student"]
                amb["similarity"] = sim
                recognized_map[sid] = amb
            else:
                # Remains ambiguous -> preserve both candidates for teacher review
                for c in unassigned_cands:
                    sid = c.get("student", {}).get("id")
                    if sid:
                        ambiguous_flagged_students[sid] = {
                            "candidate": c,
                            "detection": amb
                        }

        # 8. Compute Attendance Matrix for all division students
        attendance_records_to_save: List[LectureAttendanceModel] = []
        verified_present_count = 0
        rfid_only_count = 0
        ai_only_count = 0
        pending_count = 0
        absent_count = 0

        # Remove previous attendances for this lecture before inserting freshly verified results
        db.query(LectureAttendanceModel).filter(
            LectureAttendanceModel.lecture_session_id == lecture.id
        ).delete()
        db.commit()

        for s in div_students:
            has_rfid = s.id in daily_checked_in_ids
            has_ai = s.id in ai_verified_student_ids
            ai_conf = ai_verified_student_ids.get(s.id)
            is_ambiguous = s.id in ambiguous_flagged_students

            if has_rfid and has_ai:
                status = "PRESENT"
                source = "RFID_AND_AI"
                verified_present_count += 1
            elif has_rfid and not has_ai:
                status = "FLAGGED"
                source = "RFID_ONLY"
                rfid_only_count += 1
            elif not has_rfid and has_ai:
                status = "FLAGGED"
                source = "AI_ONLY"
                ai_only_count += 1
            elif is_ambiguous:
                status = "FLAGGED"
                source = "AMBIGUOUS_AI"
                ai_only_count += 1
            else:
                if auto_mark_absent:
                    status = "ABSENT"
                    source = "ABSENT"
                    absent_count += 1
                else:
                    status = "PENDING"
                    source = "UNVERIFIED"
                    pending_count += 1

            att = LectureAttendanceModel(
                lecture_session_id=lecture.id,
                student_id=s.id,
                status=status,
                verification_source=source,
                ai_confidence=round(ai_conf, 3) if ai_conf is not None else None,
                rfid_checked_in=has_rfid,
                ai_detected=has_ai,
                teacher_action=None,
                finalized=False
            )
            attendance_records_to_save.append(att)

        db.bulk_save_objects(attendance_records_to_save)
        db.commit()

        # 9. Build detected bounding boxes for visual overlay
        detected_boxes: List[Dict[str, Any]] = []

        for sid, rec in recognized_map.items():
            st = rec.get("student") or {}
            detected_boxes.append({
                "bbox": list(rec.get("bbox", [0, 0, 0, 0])),
                "detector_confidence": round(float(rec.get("detector_confidence", 1.0)), 3),
                "similarity": round(float(rec.get("similarity", 0.0)), 3),
                "match_status": "recognized",
                "student_id": st.get("id"),
                "student_name": st.get("name"),
                "roll_no": st.get("roll_no")
            })

        for amb in ambiguous_list:
            if amb.get("match_status") == "recognized":
                continue
            st = amb.get("student") or {}
            detected_boxes.append({
                "bbox": list(amb.get("bbox", [0, 0, 0, 0])),
                "detector_confidence": round(float(amb.get("detector_confidence", 1.0)), 3),
                "similarity": round(float(amb.get("similarity", 0.0)), 3),
                "match_status": "ambiguous",
                "student_id": st.get("id"),
                "student_name": st.get("name"),
                "roll_no": st.get("roll_no")
            })

        for unk in unknown_list:
            detected_boxes.append({
                "bbox": list(unk.get("bbox", [0, 0, 0, 0])),
                "detector_confidence": round(float(unk.get("detector_confidence", 1.0)), 3),
                "similarity": None,
                "match_status": "unknown",
                "student_id": None,
                "student_name": None,
                "roll_no": None
            })

        for dup in duplicate_list:
            st = dup.get("student") or {}
            detected_boxes.append({
                "bbox": list(dup.get("bbox", [0, 0, 0, 0])),
                "detector_confidence": round(float(dup.get("detector_confidence", 1.0)), 3),
                "similarity": round(float(dup.get("similarity", 0.0)), 3),
                "match_status": "duplicate",
                "student_id": st.get("id"),
                "student_name": st.get("name"),
                "roll_no": st.get("roll_no")
            })

        # 10. Generate annotated visual overlay
        overlay_url = None
        try:
            annotated_canvas = draw_detection_overlay(img, detected_boxes)
            success, encoded_jpg = cv2.imencode(".jpg", annotated_canvas, [cv2.IMWRITE_JPEG_QUALITY, 88])
            if success:
                overlay_info = storage_service.save_classroom_image(
                    lecture.id,
                    encoded_jpg.tobytes(),
                    f"overlay_{lecture.id}.jpg"
                )
                overlay_url = overlay_info["url"]
        except Exception as e:
            logger.warning(f"Failed to generate detection overlay: {e}")

        # Update lecture session records
        lecture.classroom_photo_url = raw_photo_url
        lecture.overlay_image_url = overlay_url
        lecture.status = "REVIEW_PENDING"
        db.commit()

        # Build attendance roster output for API response
        saved_attendances = db.query(LectureAttendanceModel).filter(
            LectureAttendanceModel.lecture_session_id == lecture.id
        ).all()

        roster_items = []
        for a in saved_attendances:
            st = division_student_map.get(a.student_id)
            roster_items.append({
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

        return {
            "lecture_id": lecture.id,
            "subject": lecture.subject,
            "division": lecture.division,
            "date": lecture.date.isoformat(),
            "daily_rfid_checked_in": len(daily_checked_in_ids),
            "ai_detected_count": len(ai_verified_student_ids),
            "verified_present": verified_present_count,
            "rfid_only": rfid_only_count,
            "ai_only": ai_only_count,
            "absent": absent_count,
            "pending": pending_count,
            "unknown_faces": len(unknown_list),
            "photo_url": raw_photo_url,
            "overlay_image_url": overlay_url,
            "detected_faces": len(detected_boxes),
            "detected_boxes": detected_boxes,
            "detector": settings.FACE_DETECTOR_MODEL,
            "attendances": roster_items
        }

    @staticmethod
    def get_review_roster(db: Session, lecture_id: int) -> List[Dict[str, Any]]:
        """Returns the formatted attendance review roster for teacher dashboard."""
        lecture = db.query(LectureSessionModel).filter(LectureSessionModel.id == lecture_id).first()
        if not lecture:
            raise EntityNotFoundError("Lecture Session", lecture_id)

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
                "ai_verification_status": "VERIFIED" if a.ai_detected else ("FLAGGED" if a.verification_source in ["RFID_ONLY", "AMBIGUOUS_AI"] else "NOT_DETECTED"),
                "confidence_score": a.ai_confidence,
                "attendance_status": a.status,
                "verification_source": a.verification_source,
                "notes": a.teacher_action
            })
        return roster

    @staticmethod
    def update_student_attendance(
        db: Session,
        lecture_id: int,
        student_id: int,
        status: str,
        reason: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """Teacher manual attendance override with audit logging."""
        lecture = db.query(LectureSessionModel).filter(LectureSessionModel.id == lecture_id).first()
        if not lecture:
            raise EntityNotFoundError("Lecture Session", lecture_id)

        if lecture.status == "FINALIZED":
            raise SessionFinalizedError(lecture.id)

        att = db.query(LectureAttendanceModel).filter(
            LectureAttendanceModel.lecture_session_id == lecture_id,
            LectureAttendanceModel.student_id == student_id
        ).first()

        if not att:
            raise EntityNotFoundError("Attendance record", student_id)

        valid_statuses = ["PRESENT", "ABSENT", "FLAGGED", "PENDING"]
        if status.upper() not in valid_statuses:
            raise SmartAttendException(400, f"Invalid status '{status}'. Must be one of {valid_statuses}")

        old_status = att.status
        new_status = status.upper()

        att.status = new_status
        att.verification_source = "TEACHER_MANUAL"
        att.teacher_action = reason or f"MANUALLY_MARKED_{new_status}"

        # Write immutable audit log
        audit = AttendanceAuditLogModel(
            user_id=str(actor_id) if actor_id else "SYSTEM",
            role=actor_role or "TEACHER",
            action=f"OVERRIDE_ATTENDANCE_{new_status}",
            entity_type="lecture_attendance",
            entity_id=str(att.id),
            _details=json.dumps({
                "lecture_id": lecture_id,
                "student_id": student_id,
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason or f"MANUALLY_MARKED_{new_status}"
            })
        )
        db.add(audit)
        db.commit()
        db.refresh(att)

        return {
            "status": "success",
            "student_id": student_id,
            "attendance_status": att.status
        }

    @staticmethod
    def finalize_lecture(
        db: Session,
        lecture_id: int,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """Engages immutable lock on lecture attendance with audit logging."""
        lecture = db.query(LectureSessionModel).filter(LectureSessionModel.id == lecture_id).first()
        if not lecture:
            raise EntityNotFoundError("Lecture Session", lecture_id)

        if lecture.status == "FINALIZED":
            raise SmartAttendException(400, "Lecture session is already FINALIZED.")

        attendances = db.query(LectureAttendanceModel).filter(
            LectureAttendanceModel.lecture_session_id == lecture_id
        ).all()

        present_cnt = 0
        absent_cnt = 0
        pending_cnt = 0

        for att in attendances:
            # Business Rule: Do NOT automatically convert PENDING into ABSENT.
            # Only explicitly confirmed absences become ABSENT.
            # Pending records remain PENDING until explicitly reviewed.
            if att.status == "PRESENT":
                present_cnt += 1
                att.finalized = True
            elif att.status == "ABSENT":
                absent_cnt += 1
                att.finalized = True
            elif att.status == "PENDING":
                pending_cnt += 1
            else:
                # Other statuses (FLAGGED, etc.)
                pass

        lecture.status = "FINALIZED"
        lecture.end_time = datetime.now(timezone.utc).time()

        # Write audit log for lecture finalization
        audit = AttendanceAuditLogModel(
            user_id=str(actor_id) if actor_id else "SYSTEM",
            role=actor_role or "TEACHER",
            action="FINALIZE_LECTURE",
            entity_type="lecture_session",
            entity_id=str(lecture.id),
            _details=json.dumps({
                "lecture_id": lecture_id,
                "present_count": present_cnt,
                "absent_count": absent_cnt,
                "pending_count": pending_cnt,
                "total_records": len(attendances)
            })
        )
        db.add(audit)
        db.commit()

        return {
            "finalized": True,
            "finalized_at": datetime.now(timezone.utc).isoformat(),
            "total_records": len(attendances),
            "present_count": present_cnt,
            "absent_count": absent_cnt,
            "pending_count": pending_cnt
        }
