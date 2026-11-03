from typing import Optional
from pydantic import BaseModel, EmailStr

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegisterPayload(BaseModel):
    role: str = "student"
    name: str
    email: EmailStr
    password: str
    teacher_id: Optional[str] = None
    department: Optional[str] = "Computer Science & Engineering"
    roll_no: Optional[str] = None
    year: Optional[str] = "3rd Year"
    division: Optional[str] = "A"
    phone: Optional[str] = None

class AuthUserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool = True
    student_id: Optional[str] = None
    class_name: Optional[str] = None
    division: Optional[str] = None

class LinkProfileResponse(BaseModel):
    status: str
    role: str
    id: int

