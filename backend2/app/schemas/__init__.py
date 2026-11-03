from app.schemas.common import APIResponse, MessageResponse
from app.schemas.auth import TokenResponse, RegisterPayload, AuthUserResponse, LinkProfileResponse
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse, StudentProfileResponse
from app.schemas.teacher import TeacherCreate, TeacherUpdate, TeacherResponse
from app.schemas.class_division import ClassDivisionCreate, ClassDivisionResponse
from app.schemas.attendance import DailyCheckinRequest, DailyCheckinResponse, DailyCheckInRecord
from app.schemas.lecture import (
    LectureCreate,
    LectureSessionResponse,
    LectureVerificationSummary,
    DetectedFaceBox,
    LectureAttendanceItem,
    AttendanceReviewItem,
    StudentAttendanceUpdate,
    FlagResolutionRequest
)
from app.schemas.face import FaceEnrollmentResponse, FaceModelInfo

__all__ = [
    "APIResponse",
    "MessageResponse",
    "TokenResponse",
    "RegisterPayload",
    "AuthUserResponse",
    "LinkProfileResponse",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "StudentCreate",
    "StudentUpdate",
    "StudentResponse",
    "StudentProfileResponse",
    "TeacherCreate",
    "TeacherUpdate",
    "TeacherResponse",
    "ClassDivisionCreate",
    "ClassDivisionResponse",
    "DailyCheckinRequest",
    "DailyCheckinResponse",
    "DailyCheckInRecord",
    "LectureCreate",
    "LectureSessionResponse",
    "LectureVerificationSummary",
    "DetectedFaceBox",
    "LectureAttendanceItem",
    "AttendanceReviewItem",
    "StudentAttendanceUpdate",
    "FlagResolutionRequest",
    "FaceEnrollmentResponse",
    "FaceModelInfo"
]

