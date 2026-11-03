from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
import app.models # Register SQLAlchemy models

# Initialize Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend microservice for AIoT SmartAttend — handling authentication, student management, face enrollment, daily RFID check-in, and per-lecture AI attendance verification.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Policy configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.student_portal import router as student_portal_router
from app.routers.students import router as students_router
from app.routers.attendance import router as attendance_router
from app.routers.lectures import router as lectures_router
from app.routers.ai import router as ai_router
from app.routers.portal_api import router as portal_router
from app.routers.rfid import router as rfid_router

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(student_portal_router)
app.include_router(students_router)
app.include_router(attendance_router)
app.include_router(lectures_router)
app.include_router(ai_router)
app.include_router(portal_router)
app.include_router(rfid_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
