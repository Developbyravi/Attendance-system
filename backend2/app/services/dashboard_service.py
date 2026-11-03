from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.student import StudentModel
from app.models.teacher import TeacherModel
from app.models.daily_checkin import DailyCheckinModel
from app.models.lecture import LectureSessionModel
from app.models.attendance import LectureAttendanceModel
from app.core.exceptions import EntityNotFoundError

class DashboardService:
    @staticmethod
    def get_admin_stats(db: Session) -> Dict[str, Any]:
        today_date = datetime.now(timezone.utc).date()

        total_students = db.query(StudentModel).filter(StudentModel.is_active == True).count()
        total_teachers = db.query(TeacherModel).filter(TeacherModel.is_active == True).count()
        today_checkins = db.query(DailyCheckinModel).filter(DailyCheckinModel.date == today_date).count()
        today_lectures = db.query(LectureSessionModel).filter(LectureSessionModel.date == today_date).count()

        total_att = db.query(LectureAttendanceModel).count()
        present_att = db.query(LectureAttendanceModel).filter(LectureAttendanceModel.status == "PRESENT").count()
        pending_flagged = db.query(LectureAttendanceModel).filter(LectureAttendanceModel.status == "FLAGGED").count()

        rate = round((present_att / total_att * 100), 1) if total_att > 0 else 0.0

        return {
            "total_students": total_students,
            "total_teachers": total_teachers,
            "today_checkins": today_checkins,
            "today_lectures": today_lectures,
            "overall_attendance_rate": rate,
            "pending_flagged_cases": pending_flagged
        }

    @staticmethod
    def get_student_stats(db: Session, student_id: int) -> Dict[str, Any]:
        student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
        if not student:
            # Also try matching user_id
            student = db.query(StudentModel).filter(StudentModel.user_id == student_id).first()
        if not student:
            raise EntityNotFoundError("Student", student_id)

        attendances = db.query(LectureAttendanceModel).filter(
            LectureAttendanceModel.student_id == student.id
        ).all()

        total = len(attendances)
        present = sum(1 for a in attendances if a.status == "PRESENT")
        absent = sum(1 for a in attendances if a.status == "ABSENT")
        flagged = sum(1 for a in attendances if a.status == "FLAGGED")

        pct = round((present / total * 100), 1) if total > 0 else 0.0

        today_date = datetime.now(timezone.utc).date()
        today_checkin = db.query(DailyCheckinModel).filter(
            DailyCheckinModel.student_id == student.id,
            DailyCheckinModel.date == today_date
        ).first()

        # Recent 10 records
        recent_records = []
        recent_atts = db.query(LectureAttendanceModel).filter(
            LectureAttendanceModel.student_id == student.id
        ).order_by(LectureAttendanceModel.id.desc()).limit(15).all()

        for a in recent_atts:
            lec = a.lecture_session
            recent_records.append({
                "date": lec.date.isoformat() if lec else "—",
                "subject": lec.subject if lec else "Lecture",
                "status": a.status,
                "teacher_name": lec.teacher.name if (lec and lec.teacher) else "Faculty"
            })

        return {
            "total_lectures": total,
            "present_count": present,
            "absent_count": absent,
            "flagged_count": flagged,
            "attendance_percentage": pct,
            "today_rfid_checked_in": today_checkin is not None,
            "today_check_in_time": today_checkin.check_in_time.strftime("%H:%M:%S") if today_checkin else None,
            "recent_records": recent_records
        }

    @staticmethod
    def get_parent_child_overview(db: Session, parent_id: int) -> Dict[str, Any]:
        # Demo/default link to active division students
        students = db.query(StudentModel).filter(StudentModel.is_active == True).limit(2).all()
        children = []
        today_date = datetime.now(timezone.utc).date()

        for s in students:
            stats = DashboardService.get_student_stats(db, s.id)
            children.append({
                "id": s.id,
                "name": s.name,
                "roll_number": s.roll_no,
                "division_name": s.division,
                "today_checked_in": stats["today_rfid_checked_in"],
                "today_time": stats["today_check_in_time"],
                "overall_percentage": stats["attendance_percentage"],
                "recent_absences": stats["absent_count"]
            })

        return {
            "children": children,
            "notifications": [
                {
                    "id": 1,
                    "title": "Daily RFID Check-In Verified",
                    "message": "Student completed campus entry tap on time.",
                    "channel": "WHATSAPP",
                    "recipient_type": "PARENT",
                    "recipient": "+919876543210",
                    "status": "SENT",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ]
        }

