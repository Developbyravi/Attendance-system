from typing import Optional
from pydantic import BaseModel

class ClassDivisionCreate(BaseModel):
    name: str
    code: Optional[str] = None
    academic_year: Optional[str] = "2026-2027"
    semester: Optional[str] = "5"
    department: Optional[str] = "Computer Science & Engineering"
    class_teacher: Optional[str] = None

class ClassDivisionResponse(BaseModel):
    id: int
    name: str
    code: str
    academic_year: str
    semester: str
    department: str
    total_students: int = 0
    class_teacher: Optional[str] = None
    is_active: bool = True

