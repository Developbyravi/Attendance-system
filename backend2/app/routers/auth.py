from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserModel
from app.schemas.auth import TokenResponse, RegisterPayload, AuthUserResponse, LinkProfileResponse
from app.core.security import verify_password, create_access_token, get_password_hash, decode_access_token
from app.core.permissions import get_current_user
from app.core.exceptions import AuthenticationError, DuplicateEntityError

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/token", response_model=TokenResponse, summary="OAuth2 Login Token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    FastAPI OAuth2 compliant form login endpoint.
    Accepts username (email or roll_no) and password.
    """
    ident = form_data.username.strip()

    user = db.query(UserModel).filter(
        (UserModel.email == ident.lower()) | (UserModel.username == ident)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password.")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact an administrator."
        )

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role, "email": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=TokenResponse, summary="User Registration")
def register(
    payload: RegisterPayload,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Unified registration endpoint.
    Public registration is strictly permitted for students.
    Creating teacher or admin accounts requires valid Admin authentication.
    """
    clean_email = payload.email.strip().lower()

    existing = db.query(UserModel).filter(UserModel.email == clean_email).first()
    if existing:
        raise DuplicateEntityError("User", "email", clean_email)

    role_str = payload.role.upper()
    if role_str in ["TEACHER", "ADMIN"]:
        auth_header = request.headers.get("Authorization")
        is_admin_auth = False
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            jwt_data = decode_access_token(token)
            if jwt_data and jwt_data.get("role", "").upper() == "ADMIN":
                is_admin_auth = True

        if not is_admin_auth:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Public registration is restricted to students. Faculty and Administrator accounts must be created by an administrator."
            )

    username = payload.roll_no or payload.teacher_id or clean_email.split("@")[0]

    user = UserModel(
        email=clean_email,
        username=username,
        full_name=payload.name,
        hashed_password=get_password_hash(payload.password),
        role=role_str,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Automatically provision linked role model
    if role_str == "STUDENT":
        from app.models.student import StudentModel
        clean_div = (payload.division or "A").replace("Div ", "").replace("Division ", "").strip()
        student = StudentModel(
            user_id=user.id,
            roll_no=payload.roll_no or f"STU-{user.id}",
            name=payload.name,
            email=clean_email,
            department=payload.department or "Computer Science & Engineering",
            year=payload.year or "3rd Year",
            division=clean_div,
            is_active=True
        )
        db.add(student)
        db.commit()

    elif role_str == "TEACHER":
        from app.models.teacher import TeacherModel
        teacher = TeacherModel(
            user_id=user.id,
            teacher_id=payload.teacher_id or f"EMP-{user.id}",
            name=payload.name,
            email=clean_email,
            department=payload.department or "Computer Science & Engineering",
            is_active=True
        )
        teacher.assigned_divisions = [payload.division or "A"]
        db.add(teacher)
        db.commit()

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role, "email": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=AuthUserResponse, summary="Get Current Authenticated User")
def get_me(current_user: UserModel = Depends(get_current_user)):
    """
    Returns profile details for currently authenticated user token.
    """
    student_id = None
    class_name = None
    division = None

    if current_user.student:
        student_id = current_user.student.roll_no
        division = current_user.student.division
        class_name = f"Div {division}"
    elif current_user.teacher:
        assigned = current_user.teacher.assigned_divisions
        division = assigned[0] if assigned else "A"
        class_name = f"Div {division}"

    return {
        "id": current_user.id,
        "username": current_user.username or current_user.email,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.lower(),
        "is_active": current_user.is_active,
        "student_id": student_id,
        "class_name": class_name,
        "division": division
    }

@router.post("/link-profile", response_model=LinkProfileResponse, summary="Link Supabase Auth Profile")
def link_profile(
    payload: RegisterPayload,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Links metadata profile after external authentication.
    """
    return {
        "status": "linked",
        "role": current_user.role.lower(),
        "id": current_user.id
    }

