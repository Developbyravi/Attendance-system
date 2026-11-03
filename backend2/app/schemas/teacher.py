from typing import Optional, List
from pydantic import BaseModel, EmailStr

class TeacherCreate(BaseModel):
    teacher_id: str
    name: str
    email: EmailStr
    department: Optional[str] = "Computer Science & Engineering"
    assigned_divisions: Optional[List[str]] = ["A"]
    password: Optional[str] = "Teacher@123"

class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    assigned_divisions: Optional[List[str]] = None
    is_active: Optional[bool] = None

class TeacherResponse(BaseModel):
    id: int
    teacher_id: str
    employee_id: Optional[str] = None
    name: str
    full_name: Optional[str] = None
    email: str
    department: str
    assigned_divisions: List[str] = []
    is_active: bool
    created_at: Optional[str] = None

