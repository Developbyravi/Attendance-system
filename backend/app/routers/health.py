from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.database import get_db
from app.services.face_recognition import get_face_recognition_service

router = APIRouter(prefix="/api", tags=["Health Check"])

@router.get("/health", summary="Health Check Endpoint")
def health_check(db: Session = Depends(get_db)):
    """
    Returns server operational status, database connectivity, and AI face model state.
    """
    db_status = "disconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"

    rec_service = get_face_recognition_service()
    model_status = "loaded" if rec_service.is_loaded else "unloaded"

    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "database": db_status,
        "face_model": model_status
    }
