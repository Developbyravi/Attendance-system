from typing import List, Optional, Tuple
from pydantic import BaseModel

class FaceEnrollmentResponse(BaseModel):
    student_id: int
    images_processed: int
    faces_detected: int
    successful_embeddings: int
    status: str
    quality_warnings: List[str] = []

class QualityCheckResult(BaseModel):
    is_valid: bool
    faces_detected: int
    brightness: float
    blur_score: float
    bbox: Optional[Tuple[int, int, int, int]] = None
    error_message: Optional[str] = None
    warnings: List[str] = []
