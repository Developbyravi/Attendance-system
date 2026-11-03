from pydantic import BaseModel, EmailStr
from typing import Optional

class TeacherRegisterSchema(BaseModel):
    teacher_id: str
    name: str
    email: EmailStr
    password: str
    department: str = "Computer Science"

class StudentRegisterSchema(BaseModel):
    roll_no: str
    name: str
    email: EmailStr
    password: str
    department: str = "Computer Science"
    year: str = "3rd Year"
    division: str = "A"
    rfid_uid: Optional[str] = None

class ParentRegisterSchema(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    password: str

class GenericRegisterSchema(BaseModel):
    role: str # "TEACHER" | "STUDENT" | "PARENT"
    name: str
    email: Optional[EmailStr] = None
    password: str
    # Teacher fields
    teacher_id: Optional[str] = None
    department: Optional[str] = "Computer Science"
    # Student fields
    roll_no: Optional[str] = None
    year: Optional[str] = "3rd Year"
    division: Optional[str] = "A"
    rfid_uid: Optional[str] = None
    # Parent fields
    phone: Optional[str] = None

class TeacherLoginSchema(BaseModel):
    email: str
    password: str

class StudentLoginSchema(BaseModel):
    email_or_roll: str
    password: str

class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user: dict

class UserProfileResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    role: str
    department: str
    roll_no: Optional[str] = None
    teacher_id: Optional[str] = None
    year: Optional[str] = None
    division: Optional[str] = None
    rfid_uid: Optional[str] = None
    face_enrolled: Optional[bool] = None

class LinkProfilePayload(BaseModel):
    role: str # "TEACHER" | "STUDENT" | "PARENT"
    name: str
    teacher_id: Optional[str] = None
    department: Optional[str] = "Computer Science"
    roll_no: Optional[str] = None
    year: Optional[str] = "3rd Year"
    division: Optional[str] = "A"
    rfid_uid: Optional[str] = None
    phone: Optional[str] = None
