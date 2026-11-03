from typing import Optional, Dict, Any
from pydantic import BaseModel

class DailyCheckinRequest(BaseModel):
    rfid_uid: str
    device_id: Optional[str] = "GATE-READER-01"

class DailyCheckinStudentSummary(BaseModel):
    id: int
    name: str
    roll_number: str
    division_name: str
    department: str

class DailyCheckinResponse(BaseModel):
    status: str # SUCCESS, ALREADY_CHECKED_IN, REJECTED
    message: str
    student: Optional[DailyCheckinStudentSummary] = None
    check_in_time: Optional[str] = None
    date: Optional[str] = None

class DailyCheckInRecord(BaseModel):
    id: int
    student_id: int
    student_name: str
    roll_number: str
    division_name: str
    rfid_uid: str
    device_id: str
    check_in_time: str
    is_verified: bool

