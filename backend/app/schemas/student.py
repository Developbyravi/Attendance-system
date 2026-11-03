from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator

class StudentBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Ravi Khile"}, description="Full name of student")
    roll_no: str = Field(..., json_schema_extra={"example": "AIML023"}, description="Unique institutional roll number")
    department: str = Field(default="Computer Science & Engineering", json_schema_extra={"example": "AI & ML"}, description="Department of study")
    year: str = Field(default="3rd Year", json_schema_extra={"example": "2nd Year"}, description="Academic year")
    division: Optional[str] = Field("A", json_schema_extra={"example": "A"}, description="Section / Division")
    email: Optional[str] = Field(None, json_schema_extra={"example": "ravi@university.edu"}, description="Student email address")
    rfid_uid: Optional[str] = Field(None, json_schema_extra={"example": "04:A3:7B:91"}, description="RFID tag UID hex format")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("name") and data.get("full_name"):
                data["name"] = data["full_name"]
            if not data.get("roll_no") and data.get("roll_number"):
                data["roll_no"] = data["roll_number"]
            if not data.get("division"):
                if data.get("division_name"):
                    data["division"] = data["division_name"]
                elif data.get("division_id"):
                    data["division"] = str(data["division_id"])
        return data

class StudentCreate(StudentBase):
    password: Optional[str] = Field(None, description="Account password for student portal login")

class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, json_schema_extra={"example": "Ravi Khile"})
    roll_no: Optional[str] = Field(None, json_schema_extra={"example": "AIML023"})
    department: Optional[str] = Field(None, json_schema_extra={"example": "AI & ML"})
    year: Optional[str] = Field(None, json_schema_extra={"example": "2nd Year"})
    division: Optional[str] = Field(None, json_schema_extra={"example": "A"})
    email: Optional[str] = Field(None, json_schema_extra={"example": "ravi@university.edu"})
    rfid_uid: Optional[str] = Field(None, json_schema_extra={"example": "04:A3:7B:91"})
    password: Optional[str] = Field(None)
    face_enrolled: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("name") and data.get("full_name"):
                data["name"] = data["full_name"]
            if not data.get("roll_no") and data.get("roll_number"):
                data["roll_no"] = data["roll_number"]
            if not data.get("division"):
                if data.get("division_name"):
                    data["division"] = data["division_name"]
                elif data.get("division_id"):
                    data["division"] = str(data["division_id"])
        return data

class StudentResponse(StudentBase):
    id: int
    face_enrolled: bool
    is_active: Optional[bool] = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
