from pydantic import BaseModel, Field
from typing import Optional

class StartAssignmentRequest(BaseModel):
    student_id: int = Field(..., description="Target student ID to assign RFID card to")
    mode: Optional[str] = Field("ASSIGN", description="Assignment mode: ASSIGN or REPLACE")
    device_id: Optional[str] = Field("GATE-READER-01", description="Target hardware reader device ID")
    timeout_seconds: Optional[int] = Field(60, ge=10, le=300, description="Session timeout in seconds (default 60s)")

class AssignmentSessionResponse(BaseModel):
    session_id: str
    student_id: int
    student_name: str
    roll_no: str
    department: str
    division: str
    current_rfid_uid: Optional[str] = None
    status: str # "PENDING_SCAN" | "SCANNED" | "CONFIRMED" | "CANCELLED" | "EXPIRED"
    scanned_uid: Optional[str] = None
    device_id: Optional[str] = None
    created_at: str
    expires_at: str
    expires_in_seconds: int
    error: Optional[str] = None

class ConfirmAssignmentRequest(BaseModel):
    session_id: str = Field(..., description="Active assignment session identifier")
    student_id: int = Field(..., description="Target student ID")
    rfid_uid: str = Field(..., description="Scanned physical card UID (e.g. 8A:3F:12:9C)")
    reason: Optional[str] = Field(None, description="Optional administrative rationale for card assignment/replacement")

class DeactivateCardRequest(BaseModel):
    student_id: int = Field(..., description="Target student ID whose card will be deactivated")
    reason: Optional[str] = Field(None, description="Administrative rationale for deactivating student card")

class DeviceRfidScanPayload(BaseModel):
    rfid_uid: str = Field(..., description="Physical RFID tag UID in hex format")
    device_id: Optional[str] = Field("GATE-READER-01", description="Ingress terminal identifier")
    mode: Optional[str] = Field(None, description="Optional explicit mode: 'assignment' or 'attendance'")
