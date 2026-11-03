from datetime import datetime, date, time, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.lecture import LectureSessionModel
from app.models.student import StudentModel
from app.models.attendance import LectureAttendanceModel
from app.core.exceptions import EntityNotFoundError

class LectureService:
    @staticmethod
    def create(db: Session, teacher_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        raw_date = data.get("lecture_date") or data.get("date")
        if raw_date:
            parsed_date = datetime.strptime(str(raw_date)[:10], "%Y-%m-%d").date()
        else:
            parsed_date = datetime.now(timezone.utc).date()

        raw_time = data.get("start_time") or "10:00"
        try:
            parts = str(raw_time).split(":")
            parsed_time = time(int(parts[0]), int(parts[1]))
        except Exception:
            parsed_time = time(10, 0)

        clean_div = str(data.get("division") or data.get("division_id") or "A").replace("Div ", "").replace("Division ", "").strip()

        lecture = LectureSessionModel(
            teacher_id=teacher_id,
            subject=data.get("subject", "General Lecture"),
            title=data.get("title") or f"{data.get('subject')} (Division {clean_div})",
            division=clean_div,
            date=parsed_date,
            start_time=parsed_time,
            classroom=data.get("classroom", "Room 101"),
            status="SCHEDULED"
        )
        db.add(lecture)
        db.commit()
        db.refresh(lecture)
        return LectureService.format_lecture_response(db, lecture)

    @staticmethod
    def get_by_id(db: Session, lecture_id: int) -> Dict[str, Any]:
        lecture = db.query(LectureSessionModel).filter(LectureSessionModel.id == lecture_id).first()
        if not lecture:
            raise EntityNotFoundError("Lecture Session", lecture_id)
        return LectureService.format_lecture_response(db, lecture)

    @staticmethod
    def list_lectures(
        db: Session,
        teacher_id: Optional[int] = None,
        target_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        q = db.query(LectureSessionModel)

        if teacher_id:
            q = q.filter(LectureSessionModel.teacher_id == teacher_id)

        if target_date:
            try:
                parsed_d = datetime.strptime(str(target_date)[:10], "%Y-%m-%d").date()
                q = q.filter(LectureSessionModel.date == parsed_d)
            except Exception:
                pass

        lectures = q.order_by(LectureSessionModel.date.desc(), LectureSessionModel.id.desc()).all()
        return [LectureService.format_lecture_response(db, l) for l in lectures]

    @staticmethod
    def format_lecture_response(db: Session, lecture: LectureSessionModel) -> Dict[str, Any]:
        attendances = db.query(LectureAttendanceModel).filter(
            LectureAttendanceModel.lecture_session_id == lecture.id
        ).all()

        present_cnt = sum(1 for a in attendances if a.status == "PRESENT")
        absent_cnt = sum(1 for a in attendances if a.status == "ABSENT")
        flagged_cnt = sum(1 for a in attendances if a.status == "FLAGGED")
        pending_cnt = sum(1 for a in attendances if a.status == "PENDING")

        # Total enrolled in division if attendance has not been recorded yet
        if not attendances:
            clean_div = lecture.division
            total_enrolled = db.query(StudentModel).filter(
                or_(
                    StudentModel.division == clean_div,
                    StudentModel.division == f"Div {clean_div}",
                    StudentModel.division == f"Division {clean_div}"
                ),
                StudentModel.is_active == True
            ).count()
        else:
            total_enrolled = len(attendances)

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

        return {
            "id": lecture.id,
            "teacher_id": lecture.teacher_id,
            "teacher_name": lecture.teacher.name if lecture.teacher else "Faculty Member",
            "subject": lecture.subject,
            "title": lecture.title or f"{lecture.subject} (Division {lecture.division})",
            "division": lecture.division,
            "division_id": lecture.division,
            "division_name": f"Division {lecture.division}",
            "lecture_date": lecture.date.isoformat(),
            "date": lecture.date.isoformat(),
            "start_time": lecture.start_time.strftime("%H:%M") if lecture.start_time else "10:00",
            "end_time": lecture.end_time.strftime("%H:%M") if lecture.end_time else None,
            "classroom": lecture.classroom or "Room 101",
            "status": lecture.status.lower(),
            "raw_status": lecture.status,
            "classroom_photo_url": lecture.classroom_photo_url,
            "overlay_image_url": lecture.overlay_image_url,
            "total_enrolled": total_enrolled,
            "present_count": present_cnt,
            "absent_count": absent_cnt,
            "flagged_count": flagged_cnt,
            "pending_count": pending_cnt,
            "finalized_at": datetime.now(timezone.utc).isoformat() if lecture.status == "FINALIZED" else None,
            "created_at": lecture.created_at.isoformat(),
            "attendances": att_items
        }

