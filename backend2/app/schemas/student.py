from typing import Optional, Any
from pydantic import BaseModel, EmailStr

class StudentCreate(BaseModel):
    roll_no: str
    name: str
    email: EmailStr
    department: Optional[str] = "Computer Science & Engineering"
    year: Optional[str] = "3rd Year"
    division: Optional[str] = "A"
    division_id: Optional[Any] = None
    rfid_uid: Optional[str] = None
    password: Optional[str] = "Student@123"

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    year: Optional[str] = None
    division: Optional[str] = None
    division_id: Optional[Any] = None
    rfid_uid: Optional[str] = None
    is_active: Optional[bool] = None

class StudentResponse(BaseModel):
    id: int
    roll_no: str
    roll_number: Optional[str] = None
    name: str
    full_name: Optional[str] = None
    email: str
    department: str
    year: str
    division: str
    division_id: Optional[Any] = None
    division_name: Optional[str] = None
    class_name: Optional[str] = None
    rfid_uid: Optional[str] = None
    face_enrolled: bool
    is_active: bool
    created_at: Optional[str] = None

class StudentProfileResponse(BaseModel):
    id: int
    name: str
    roll_no: str
    email: str
    department: str
    year: str
    division: str
    rfid_uid: Optional[str] = None
    face_enrolled: bool
    created_at: str
