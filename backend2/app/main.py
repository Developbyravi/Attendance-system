import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.logging import logger
from app.core.exceptions import SmartAttendException
from app.database import init_db, SessionLocal
from app.models.user import UserModel
from app.core.security import get_password_hash
from app.ai.recognizer import FaceRecognitionPipeline

# Routers
from app.routers.auth import router as auth_router
from app.routers.students import router as students_router
from app.routers.teachers import router as teachers_router
from app.routers.lectures import router as lectures_router
from app.routers.attendance import router as attendance_router
from app.routers.rfid import router as rfid_router
from app.routers.portal import router as portal_router
from app.routers.health import router as health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle management.
    """
    logger.info(f"Starting {settings.APP_TITLE} v{settings.APP_VERSION} on {settings.APP_HOST}:{settings.APP_PORT}...")

    # 1. Initialize database schema
    init_db()

    # 2. Seed initial default administrator if not present
    db = SessionLocal()
    try:
        admin_email = "admin@smartattend.edu"
        admin = db.query(UserModel).filter(UserModel.email == admin_email).first()
        if not admin:
            admin = UserModel(
                email=admin_email,
                username="admin",
                full_name="System Administrator",
                hashed_password=get_password_hash("Admin@123"),
                role="ADMIN",
                is_active=True
            )
            db.add(admin)
            db.commit()
            logger.info("Default administrator seeded (admin@smartattend.edu / Admin@123)")
    finally:
        db.close()

    # 3. Warm up InsightFace SCRFD-10G & ArcFace AI Pipeline
    try:
        pipeline = FaceRecognitionPipeline.get_instance()
        info = pipeline.get_model_info()
        logger.info(
            f"AI Pipeline Ready: Detector='{info['detector']}' (Loaded: {info['detector_loaded']}, "
            f"Provider: {info['active_provider']}), Recognizer='{info['model']}' ({info['embedding_dimension']}-D)"
        )
    except Exception as e:
        logger.error(f"Failed to pre-warm AI engine: {e}")

    yield

    logger.info("Application shutting down.")

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="SmartAttend AIoT Backend2 — High-Performance Face Recognition & RFID Attendance Architecture",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Uploads directory for static photo serving
upload_path = settings.resolved_upload_dir
os.makedirs(upload_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_path), name="uploads")

# Global Exception Handlers
@app.exception_handler(SmartAttendException)
async def smartattend_exception_handler(request: Request, exc: SmartAttendException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.error_code,
            "detail": exc.detail,
            "data": exc.data
        }
    )

# Include Routers under /api
api_prefix = "/api"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(students_router, prefix=api_prefix)
app.include_router(teachers_router, prefix=api_prefix)
app.include_router(lectures_router, prefix=api_prefix)
app.include_router(attendance_router, prefix=api_prefix)
app.include_router(rfid_router, prefix=api_prefix)
app.include_router(portal_router, prefix=api_prefix)
app.include_router(health_router, prefix=api_prefix)

# Also expose direct root health check
app.include_router(health_router)

