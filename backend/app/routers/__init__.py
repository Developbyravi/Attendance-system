from app.routers.health import router as health_router
from app.routers.students import router as students_router
from app.routers.attendance import router as attendance_router
from app.routers.ai import router as ai_router
from app.routers.auth import router as auth_router
from app.routers.student_portal import router as student_portal_router
from app.routers.lectures import router as lectures_router

__all__ = [
    "health_router",
    "students_router",
    "attendance_router",
    "ai_router",
    "auth_router",
    "student_portal_router",
    "lectures_router"
]
