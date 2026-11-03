from typing import Optional
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    password: str
    full_name: str
    role: str = "STUDENT"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    full_name: str
    role: str
    is_active: bool
    created_at: Optional[str] = None

