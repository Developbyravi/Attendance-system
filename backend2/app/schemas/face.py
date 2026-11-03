from typing import Optional, List
from pydantic import BaseModel

class FaceEnrollmentResponse(BaseModel):
    student_id: int
    images_processed: int = 1
    faces_detected: int = 1
    successful_embeddings: int = 1
    status: str = "success"
    quality_warnings: List[str] = []

class FaceModelInfo(BaseModel):
    model: str
    detector: str
    embedding_dimension: int
    recognition_threshold: float
    ambiguity_threshold: float
    status: str

