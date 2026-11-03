from app.database import get_db
from app.core.permissions import (
    get_current_user,
    require_admin,
    require_teacher,
    require_student,
    get_current_teacher,
    get_current_student
)

__all__ = [
    "get_db",
    "get_current_user",
    "require_admin",
    "require_teacher",
    "require_student",
    "get_current_teacher",
    "get_current_student"
]

