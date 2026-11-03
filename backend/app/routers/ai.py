from fastapi import APIRouter
from app.services.face_recognition import get_face_recognition_service

router = APIRouter(prefix="/api/ai", tags=["AI Model Info"])

@router.get("/model-info", summary="Get AI Face Recognition Model Info")
def get_model_info():
    """
    Returns active face recognition model metadata, dimension, detector backend, and confidence threshold.
    """
    service = get_face_recognition_service()
    return service.get_model_info()
