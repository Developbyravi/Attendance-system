from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class LectureCreate(BaseModel):
    subject: str
    title: Optional[str] = None
    division_id: Optional[Any] = "A"
    division: Optional[str] = "A"
    lecture_date: Optional[str] = None
    date: Optional[str] = None
    start_time: Optional[str] = "10:00"
    end_time: Optional[str] = None
    classroom: Optional[str] = "Room 101"

class LectureSessionResponse(BaseModel):
    id: int
    title: str
    subject: str
    division_id: Any
    division_name: str
    division: str
    teacher_id: int
    teacher_name: Optional[str] = None
    lecture_date: str
    date: str
    start_time: str
    end_time: Optional[str] = None
    classroom: Optional[str] = "Room 101"
    status: str # scheduled, in_progress, review_pending, finalized
    raw_status: Optional[str] = "SCHEDULED"
    classroom_photo_url: Optional[str] = None
    overlay_image_url: Optional[str] = None
    total_enrolled: int = 0
    present_count: int = 0
    absent_count: int = 0
    flagged_count: int = 0
    pending_count: int = 0
    finalized_at: Optional[str] = None
    created_at: Optional[str] = None
    attendances: Optional[List[Dict[str, Any]]] = None

class DetectedFaceBox(BaseModel):
    bbox: List[int] # [x, y, w, h]
    detector_confidence: float
    similarity: Optional[float] = None
    match_status: str # recognized, ambiguous, unknown, duplicate
    student_id: Optional[int] = None
    student_name: Optional[str] = None
    roll_no: Optional[str] = None

class LectureAttendanceItem(BaseModel):
    id: int
    lecture_session_id: int
    student_id: int
    student_name: str
    roll_no: str
    department: str
    division: str
    status: str # PRESENT, FLAGGED, PENDING, ABSENT
    verification_source: str
    ai_confidence: Optional[float] = None
    rfid_checked_in: bool = False
    ai_detected: bool = False
    teacher_action: Optional[str] = None
    finalized: bool = False

class LectureVerificationSummary(BaseModel):
    lecture_id: int
    subject: str
    division: str
    date: str
    daily_rfid_checked_in: int
    ai_detected_count: int
    verified_present: int
    rfid_only: int
    ai_only: int
    absent: int
    pending: int = 0
    unknown_faces: int = 0
    photo_url: Optional[str] = None
    overlay_image_url: Optional[str] = None
    detected_faces: int = 0
    detected_boxes: List[DetectedFaceBox] = []
    detector: str = "InsightFace SCRFD-10G"
    attendances: List[Dict[str, Any]] = []

class AttendanceReviewItem(BaseModel):
    id: int
    student_id: int
    student_name: str
    roll_number: str
    daily_rfid_status: str # CHECKED_IN, NOT_CHECKED_IN
    daily_check_in_time: Optional[str] = None
    ai_verification_status: str # VERIFIED, UNKNOWN, NOT_DETECTED, FLAGGED
    confidence_score: Optional[float] = None
    attendance_status: str # PRESENT, ABSENT, FLAGGED, PENDING
    verification_source: str
    notes: Optional[str] = None

class StudentAttendanceUpdate(BaseModel):
    status: str # PRESENT, ABSENT, FLAGGED
    reason: Optional[str] = None

class FlagResolutionRequest(BaseModel):
    student_id: int
    action: str # CONFIRM_PRESENT, MARK_ABSENT

