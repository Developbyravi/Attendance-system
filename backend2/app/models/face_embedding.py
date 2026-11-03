import json
from datetime import datetime, timezone
from typing import List
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class FaceEmbeddingModel(Base):
    __tablename__ = "face_embeddings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    _embedding = Column("embedding", Text, nullable=False) # JSON encoded list of 512 floats
    image_reference = Column(String(255), nullable=True)
    quality_score = Column(Float, nullable=True, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    student = relationship("StudentModel", back_populates="face_embeddings")

    @property
    def embedding_list(self) -> List[float]:
        try:
            return json.loads(self._embedding)
        except Exception:
            return []

    @embedding_list.setter
    def embedding_list(self, val: List[float]):
        self._embedding = json.dumps(val)

    @property
    def embedding(self) -> str:
        return self._embedding

    @embedding.setter
    def embedding(self, val: str):
        self._embedding = val

    def __repr__(self):
        return f"<FaceEmbedding id={self.id} student_id={self.student_id}>"

