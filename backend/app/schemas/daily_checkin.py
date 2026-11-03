from pydantic import BaseModel
from typing import Optional, List

class RfidCheckinRequest(BaseModel):
    rfid_uid: str
    device_id: Optional[str] = None

class DailyCheckinResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    roll_no: str
    date: str
    scan_time: str
    status: str

class DailyCheckinSummaryStudent(BaseModel):
    id: int
    student_id: int
    student_name: str
    roll_no: str
    department: str
    division: str
    scan_time: str
    scan_count: int

class DailyCheckinSummaryResponse(BaseModel):
    date: str
    checked_in: int
    total_students: int
    percentage: float
    students: List[DailyCheckinSummaryStudent]
