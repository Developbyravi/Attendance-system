import os
import uuid
import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    """
    Storage Service with local filesystem persistence and optional Supabase Storage driver.
    """
    def __init__(self):
        self.upload_dir = settings.resolved_upload_dir
        self.classroom_dir = os.path.join(self.upload_dir, "classroom")
        self.students_dir = os.path.join(self.upload_dir, "students")
        os.makedirs(self.classroom_dir, exist_ok=True)
        os.makedirs(self.students_dir, exist_ok=True)

    def save_classroom_image(
        self,
        lecture_id: int,
        file_bytes: bytes,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Saves a classroom photograph locally."""
        ext = ".jpg"
        if filename and "." in filename:
            ext = os.path.splitext(filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            ext = ".jpg"

        unique_id = uuid.uuid4().hex[:12]
        file_name = f"lecture_{lecture_id}_{unique_id}{ext}"
        target_path = os.path.join(self.classroom_dir, file_name)

        with open(target_path, "wb") as f:
            f.write(file_bytes)

        # Public URL served by FastAPI static mount
        url = f"/uploads/classroom/{file_name}"
        return {
            "path": target_path,
            "filename": file_name,
            "url": url,
            "driver": "local"
        }

    def save_student_image(
        self,
        student_id: int,
        file_bytes: bytes,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Saves a student enrollment photo locally."""
        ext = ".jpg"
        if filename and "." in filename:
            ext = os.path.splitext(filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            ext = ".jpg"

        unique_id = uuid.uuid4().hex[:12]
        file_name = f"student_{student_id}_{unique_id}{ext}"
        target_path = os.path.join(self.students_dir, file_name)

        with open(target_path, "wb") as f:
            f.write(file_bytes)

        url = f"/uploads/students/{file_name}"
        return {
            "path": target_path,
            "filename": file_name,
            "url": url,
            "driver": "local"
        }

default_storage_service = StorageService()

def get_storage_service() -> StorageService:
    return default_storage_service

