from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, Union
from datetime import date as dt_date, datetime as dt_datetime

class LectureCreate(BaseModel):
    subject: str
    division: Optional[str] = None
    division_id: Optional[Any] = None
    title: Optional[str] = None
    date: Optional[Union[dt_date, str]] = None
    lecture_date: Optional[Union[dt_date, str]] = None
    start_time: Optional[str] = None
    classroom: Optional[str] = None

class LectureResponse(BaseModel):
    id: int
    teacher_id: int
    teacher_name: Optional[str] = None
    subject: str
    division: str
    division_name: Optional[str] = None
    division_id: Optional[Any] = None
    title: Optional[str] = None
    date: dt_date
    lecture_date: Optional[str] = None
    start_time: Any
    end_time: Optional[Any] = None
    classroom: Optional[str] = None
    status: str
    classroom_photo_url: Optional[str] = None
    overlay_image_url: Optional[str] = None
    total_enrolled: Optional[int] = 0
    present_count: Optional[int] = 0
    absent_count: Optional[int] = 0
    flagged_count: Optional[int] = 0
    pending_count: Optional[int] = 0
    finalized_at: Optional[str] = None
    created_at: dt_datetime

    model_config = ConfigDict(from_attributes=True)

class LectureAttendanceItem(BaseModel):
    id: int
    lecture_session_id: int
    student_id: int
    student_name: str
    roll_no: str
    department: str
    division: str
    status: str
    verification_source: str
    ai_confidence: Optional[float] = None
    rfid_checked_in: bool
    ai_detected: bool
    teacher_action: Optional[str] = None
    finalized: bool

    model_config = ConfigDict(from_attributes=True)

class DetectedFaceBox(BaseModel):
    bbox: List[int] # [x, y, w, h]
    detector_confidence: float
    similarity: Optional[float] = None
    match_status: str # "recognized", "ambiguous", "unknown", "duplicate"
    student_id: Optional[int] = None
    student_name: Optional[str] = None
    roll_no: Optional[str] = None

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
    pending: Optional[int] = 0
    unknown_faces: int
    attendances: List[LectureAttendanceItem]
    photo_url: Optional[str] = None
    overlay_image_url: Optional[str] = None
    detected_faces: Optional[int] = None
    detected_boxes: Optional[List[DetectedFaceBox]] = []
    detector: Optional[str] = "InsightFace SCRFD-10G"

class FlagResolutionRequest(BaseModel):
    student_id: int
    action: str

class StudentAttendanceUpdate(BaseModel):
    status: str
    reason: Optional[str] = None
