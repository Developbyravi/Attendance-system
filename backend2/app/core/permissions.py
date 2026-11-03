from typing import List, Optional
from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserModel
from app.models.teacher import TeacherModel
from app.models.student import StudentModel
from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationError, AuthorizationError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

def get_token_from_header(
    authorization: Optional[str] = Header(None),
    token_from_oauth: Optional[str] = Depends(oauth2_scheme)
) -> str:
    """Extracts bearer token from Authorization header or OAuth2 scheme."""
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    if token_from_oauth:
        return token_from_oauth.strip()
    raise AuthenticationError("Authentication token is missing. Please log in.")

def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db)
) -> UserModel:
    """Validates JWT and returns current active UserModel."""
    payload = decode_access_token(token)
    email: Optional[str] = payload.get("email") or payload.get("sub")
    user_id: Optional[str] = payload.get("user_id") or payload.get("id")

    query = db.query(UserModel)
    user = None
    if user_id and str(user_id).isdigit():
        user = query.filter(UserModel.id == int(user_id)).first()
    if not user and email:
        user = query.filter(UserModel.email == email).first()

    if not user:
        raise AuthenticationError("User associated with this token does not exist.")

    if not user.is_active:
        raise AuthorizationError("Account is inactive. Please contact administration.")

    return user

def require_role(allowed_roles: List[str]):
    """Enforces specific user role membership."""
    normalized_allowed = [r.upper() for r in allowed_roles]

    def role_checker(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        user_role = current_user.role.upper()
        if user_role not in normalized_allowed and "ADMIN" not in normalized_allowed:
            raise AuthorizationError(f"Access forbidden: Requires one of roles {allowed_roles}")
        return current_user

    return role_checker

def require_admin(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """Enforces ADMIN privileges."""
    if current_user.role.upper() != "ADMIN":
        raise AuthorizationError("Access forbidden: Administrator privileges required.")
    return current_user

def require_teacher(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """Enforces TEACHER or ADMIN privileges."""
    if current_user.role.upper() not in ["TEACHER", "ADMIN"]:
        raise AuthorizationError("Access forbidden: Faculty or Administrator privileges required.")
    return current_user

def require_student(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """Enforces STUDENT or ADMIN privileges."""
    if current_user.role.upper() not in ["STUDENT", "ADMIN"]:
        raise AuthorizationError("Access forbidden: Student privileges required.")
    return current_user

def get_current_teacher(
    current_user: UserModel = Depends(require_teacher),
    db: Session = Depends(get_db)
) -> TeacherModel:
    """Returns the TeacherModel linked to the current authenticated teacher/admin."""
    teacher = db.query(TeacherModel).filter(
        (TeacherModel.user_id == current_user.id) | (TeacherModel.email == current_user.email)
    ).first()

    if not teacher:
        # Auto-provision teacher record for admin if not existing
        if current_user.role.upper() == "ADMIN":
            teacher = TeacherModel(
                user_id=current_user.id,
                teacher_id=f"ADM-{current_user.id}",
                name=current_user.full_name or "Administrator",
                email=current_user.email,
                department="Computer Science & Engineering",
                is_active=True
            )
            teacher.assigned_divisions = ["A", "B"]
            db.add(teacher)
            db.commit()
            db.refresh(teacher)
        else:
            raise AuthorizationError("Teacher profile record not found for this account.")

    return teacher

def get_current_student(
    current_user: UserModel = Depends(require_student),
    db: Session = Depends(get_db)
) -> StudentModel:
    """Returns the StudentModel linked to the current authenticated student."""
    student = db.query(StudentModel).filter(
        (StudentModel.user_id == current_user.id) | (StudentModel.email == current_user.email)
    ).first()

    if not student:
        raise AuthorizationError("Student profile record not found for this account.")

    return student

