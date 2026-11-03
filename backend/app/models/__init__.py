from app.models.student import StudentModel
from app.models.teacher import TeacherModel
from app.models.face_embedding import FaceEmbeddingModel
from app.models.session import AttendanceSessionModel
from app.models.rfid_event import RfidEventModel
from app.models.ai_detection import AiFaceDetectionModel
from app.models.verification import AttendanceVerificationModel
from app.models.record import AttendanceRecordModel
from app.models.daily_checkin import DailyCheckinModel
from app.models.lecture_session import LectureSessionModel
from app.models.lecture_attendance import LectureAttendanceModel
from app.models.parent import ParentModel, ParentStudentModel
from app.models.audit_log import AuditLogModel

from app.models.device import DeviceModel
from app.models.division import DivisionModel

__all__ = [
    "StudentModel",
    "TeacherModel",
    "FaceEmbeddingModel",
    "AttendanceSessionModel",
    "RfidEventModel",
    "AiFaceDetectionModel",
    "AttendanceVerificationModel",
    "AttendanceRecordModel",
    "DailyCheckinModel",
    "LectureSessionModel",
    "LectureAttendanceModel",
    "ParentModel",
    "ParentStudentModel",
    "AuditLogModel",
    "DeviceModel",
    "DivisionModel"
]
