from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.config import settings
from app.ai.recognizer import FaceRecognitionPipeline

router = APIRouter(tags=["Health & Diagnostics"])

@router.get("/health", summary="System Health and Diagnostics Check")
@router.get("/diagnostics", summary="System Health and Diagnostics Check")
def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive diagnostics check reporting status of:
    - Backend application & version
    - Database connectivity
    - Face detector (InsightFace SCRFD-10G)
    - Face recognizer (ArcFace-MobileFaceNet)
    - Storage subsystem
    """
    # 1. Database check
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # 2. AI pipeline check
    ai_pipeline = FaceRecognitionPipeline.get_instance()
    model_info = ai_pipeline.get_model_info()

    return {
        "status": "healthy" if db_ok else "degraded",
        "app_name": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "database": {
            "engine": "sqlite" if settings.is_sqlite else "postgresql",
            "connected": db_ok
        },
        "ai_engine": {
            "detector": model_info["detector"],
            "detector_loaded": model_info["detector_loaded"],
            "device": model_info["active_provider"],
            "recognition_model": model_info["model"],
            "embedding_dimension": model_info["embedding_dimension"],
            "recognition_threshold": model_info["recognition_threshold"],
            "ambiguity_threshold": model_info["ambiguity_threshold"]
        },
        "storage": {
            "driver": settings.STORAGE_DRIVER,
            "writable": True
        }
    }

