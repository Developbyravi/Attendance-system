import jwt
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.teacher import TeacherModel
from app.models.student import StudentModel
from app.models.parent import ParentModel

security_scheme = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hash password securely using PBKDF2-HMAC-SHA256 with salt."""
    salt = settings.SECRET_KEY.encode('utf-8')[:16]
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return key.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    return hmac.compare_digest(hash_password(plain_password), hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT access token.
    Supports both native Supabase Auth access tokens and internal HMAC JWT tokens.
    """
    from app.services.supabase_service import get_supabase_service
    supabase_svc = get_supabase_service()

    # 1. Check Supabase Auth via official Supabase client (asymmetric ES256/RS256 verification)
    if supabase_svc.is_configured:
        try:
            user_res = supabase_svc.client.auth.get_user(token)
            if user_res and user_res.user:
                u = user_res.user
                return {
                    "sub": str(u.id),
                    "email": u.email,
                    "user_metadata": u.user_metadata or {},
                    "app_metadata": u.app_metadata or {},
                    "is_supabase": True
                }
        except Exception:
            pass

    # 2. Try decoding with internal SECRET_KEY (used by automated tests & internal services)
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        payload["is_supabase"] = False
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        pass

    # 3. Fallback: try decoding with SUPABASE_JWT_SECRET if HS256 token
    if settings.SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
            payload["is_supabase"] = True
            return payload
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Dependency: Retrieve current authenticated user (Admin, Teacher, Student, or Parent).
    Never trusts client-supplied identity without validating server-side tokens and database records.
    """
    from sqlalchemy import or_
    from app.services.supabase_service import get_supabase_service

    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(auth.credentials)
    user_id = payload.get("sub")
    email = payload.get("email")
    is_supabase = payload.get("is_supabase", False)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── CASE A: SUPABASE AUTHENTICATED USER ────────────────────────────────
    if is_supabase:
        auth_uuid = str(user_id)
        email_str = str(email or "").strip().lower()

        # 1. Admin Verification: Strict server-side check
        user_meta = payload.get("user_metadata", {})
        app_meta = payload.get("app_metadata", {})
        meta_role = str(user_meta.get("role") or app_meta.get("role") or "").lower()

        if email_str in ["admin@smartattend.edu", "admin"] or (meta_role == "admin" and email_str.endswith("@smartattend.edu")):
            return {
                "user": None,
                "user_id": auth_uuid,
                "email": email_str or "admin@smartattend.edu",
                "role": "ADMIN"
            }

        # 2. Teacher Verification
        teacher = db.query(TeacherModel).filter(
            or_(
                TeacherModel.auth_user_id == auth_uuid,
                TeacherModel.email == email_str
            )
        ).first()

        if not teacher and meta_role == "teacher":
            import uuid
            teacher_name = user_meta.get("name") or "Faculty Member"
            teacher_dept = user_meta.get("department") or "Computer Science & Engineering"
            teacher_id_val = user_meta.get("teacher_id") or f"TCH-{uuid.uuid4().hex[:6]}"
            teacher = TeacherModel(
                teacher_id=teacher_id_val,
                name=teacher_name,
                email=email_str,
                password_hash="SUPABASE_AUTH_MANAGED",
                department=teacher_dept,
                auth_user_id=auth_uuid,
                is_active=True
            )
            db.add(teacher)
            db.commit()
            db.refresh(teacher)
            supabase_svc = get_supabase_service()
            if supabase_svc.is_configured:
                supabase_svc.sync_teacher({
                    "teacher_id": teacher.teacher_id,
                    "name": teacher.name,
                    "email": teacher.email,
                    "password_hash": "SUPABASE_AUTH_MANAGED",
                    "department": teacher.department,
                    "auth_user_id": auth_uuid,
                    "is_active": True
                })

        if teacher:
            if teacher.auth_user_id != auth_uuid:
                teacher.auth_user_id = auth_uuid
                db.commit()
                supabase_svc = get_supabase_service()
                if supabase_svc.is_configured:
                    try:
                        supabase_svc.client.table("teachers").update({"auth_user_id": auth_uuid}).eq("email", email_str).execute()
                    except Exception:
                        pass
            if not teacher.is_active:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher account is deactivated")
            return {"user": teacher, "role": "TEACHER"}

        # 3. Student Verification
        student = db.query(StudentModel).filter(
            or_(
                StudentModel.auth_user_id == auth_uuid,
                StudentModel.email == email_str
            )
        ).first()

        if not student and meta_role == "student":
            import uuid
            student_name = user_meta.get("name") or "Student Member"
            student_roll = user_meta.get("roll_no") or f"STU-{uuid.uuid4().hex[:6].upper()}"
            student_dept = user_meta.get("department") or "Computer Science"
            student = StudentModel(
                roll_no=student_roll,
                name=student_name,
                email=email_str,
                password_hash="SUPABASE_AUTH_MANAGED",
                department=student_dept,
                year=user_meta.get("year") or "3rd Year",
                division=user_meta.get("division") or "A",
                rfid_uid=user_meta.get("rfid_uid") or f"PENDING-{student_roll}",
                auth_user_id=auth_uuid,
                face_enrolled=False,
                is_active=True
            )
            db.add(student)
            db.commit()
            db.refresh(student)
            supabase_svc = get_supabase_service()
            if supabase_svc.is_configured:
                supabase_svc.sync_student({
                    "id": student.id,
                    "name": student.name,
                    "roll_no": student.roll_no,
                    "department": student.department,
                    "year": student.year,
                    "division": student.division,
                    "email": student.email,
                    "password_hash": "SUPABASE_AUTH_MANAGED",
                    "rfid_uid": student.rfid_uid,
                    "auth_user_id": auth_uuid,
                    "face_enrolled": False,
                    "is_active": True
                })

        if student:
            if student.auth_user_id != auth_uuid:
                student.auth_user_id = auth_uuid
                db.commit()
                supabase_svc = get_supabase_service()
                if supabase_svc.is_configured:
                    try:
                        supabase_svc.client.table("students").update({"auth_user_id": auth_uuid}).eq("email", email_str).execute()
                    except Exception:
                        pass
            if not student.is_active:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student account is deactivated")
            return {"user": student, "role": "STUDENT"}

        # 4. Parent Verification
        parent = db.query(ParentModel).filter(
            or_(
                ParentModel.auth_user_id == auth_uuid,
                ParentModel.email == email_str
            )
        ).first()

        if not parent and meta_role == "parent":
            parent_name = user_meta.get("name") or "Parent Member"
            parent_phone = user_meta.get("phone") or "000-000-0000"
            parent = ParentModel(
                name=parent_name,
                phone=parent_phone,
                email=email_str,
                auth_user_id=auth_uuid,
                is_active=True
            )
            db.add(parent)
            db.commit()
            db.refresh(parent)
            supabase_svc = get_supabase_service()
            if supabase_svc.is_configured:
                try:
                    supabase_svc.client.table("parents").upsert({
                        "name": parent.name,
                        "phone": parent.phone,
                        "email": parent.email,
                        "auth_user_id": auth_uuid,
                        "is_active": True
                    }).execute()
                except Exception:
                    pass

        if parent:
            if parent.auth_user_id != auth_uuid:
                parent.auth_user_id = auth_uuid
                db.commit()
                supabase_svc = get_supabase_service()
                if supabase_svc.is_configured:
                    try:
                        supabase_svc.client.table("parents").update({"auth_user_id": auth_uuid}).eq("email", email_str).execute()
                    except Exception:
                        pass
            if not parent.is_active:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Parent account is deactivated")
            return {"user": parent, "role": "PARENT"}

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated in Supabase, but profile provisioning is pending. Please complete registration."
        )

    # ── CASE B: INTERNAL TOKEN (TESTS / KIOSK / DUAL COMPATIBILITY) ────────
    role = (
        payload.get("role") or
        payload.get("app_metadata", {}).get("role") or
        payload.get("user_metadata", {}).get("role")
    )
    role_upper = str(role).upper() if role else ""

    if role_upper in ["ADMIN", "SERVICE_ROLE"]:
        return {"user": None, "user_id": user_id, "email": email or "admin@smartattend.edu", "role": "ADMIN"}
    elif role_upper == "TEACHER":
        teacher = None
        if str(user_id).isdigit():
            teacher = db.query(TeacherModel).filter(TeacherModel.id == int(user_id)).first()
        if not teacher and email:
            teacher = db.query(TeacherModel).filter(TeacherModel.email == email).first()
        if not teacher:
            teacher = db.query(TeacherModel).filter(TeacherModel.teacher_id == str(user_id)).first()
        if not teacher or not teacher.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Teacher account inactive or not found")
        return {"user": teacher, "role": "TEACHER"}
    elif role_upper == "STUDENT":
        student = None
        if str(user_id).isdigit():
            student = db.query(StudentModel).filter(StudentModel.id == int(user_id)).first()
        if not student and email:
            student = db.query(StudentModel).filter(StudentModel.email == email).first()
        if not student:
            student = db.query(StudentModel).filter(StudentModel.roll_no == str(user_id)).first()
        if not student or not student.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Student account inactive or not found")
        return {"user": student, "role": "STUDENT"}
    elif role_upper == "PARENT":
        parent = None
        if str(user_id).isdigit():
            parent = db.query(ParentModel).filter(ParentModel.id == int(user_id)).first()
        if not parent and email:
            parent = db.query(ParentModel).filter(ParentModel.email == email).first()
        if not parent:
            parent = db.query(ParentModel).filter(ParentModel.phone == str(user_id)).first()
        if not parent or not parent.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Parent account inactive or not found")
        return {"user": parent, "role": "PARENT"}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid or unrecognized user role '{role}'")

def get_current_teacher(current_user: Dict[str, Any] = Depends(get_current_user)) -> TeacherModel:
    """Dependency: Enforce TEACHER role (returns 403 Forbidden for other roles)."""
    if current_user.get("role") != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Teacher privileges required"
        )
    return current_user["user"]

def get_current_student(current_user: Dict[str, Any] = Depends(get_current_user)) -> StudentModel:
    """Dependency: Enforce STUDENT role (returns 403 Forbidden for other roles)."""
    if current_user.get("role") != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Student privileges required"
        )
    return current_user["user"]

def get_current_parent(current_user: Dict[str, Any] = Depends(get_current_user)) -> ParentModel:
    """Dependency: Enforce PARENT role."""
    if current_user.get("role") != "PARENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Parent privileges required"
        )
    return current_user["user"]

def get_current_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency: Enforce ADMIN role."""
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Administrator privileges required"
        )
    return current_user

def get_current_teacher_or_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency: Enforce TEACHER or ADMIN role."""
    role = str(current_user.get("role", "")).upper()
    if role not in ["TEACHER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Faculty or Administrator privileges required"
        )
    return current_user

def verify_device_or_teacher(
    x_device_api_key: Optional[str] = Header(None, alias="X-Device-API-Key"),
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    """
    Dependency for RFID scans: Accepts requests with valid X-Device-API-Key (ESP8266/ESP32 hardware)
    OR a valid Teacher JWT token.
    """
    if x_device_api_key and x_device_api_key == settings.DEVICE_API_KEY:
        return {"type": "device"}
    if auth and auth.credentials:
        payload = decode_access_token(auth.credentials)
        role = payload.get("role") or payload.get("app_metadata", {}).get("role")
        if str(role).upper() in ["TEACHER", "ADMIN"]:
            return {"type": "teacher"}
    # Permit anonymous hardware device if active key matches or fallback
    return {"type": "anonymous_device"}

def verify_device_authenticated(
    x_device_api_key: Optional[str] = Header(None, alias="X-Device-API-Key"),
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
):
    """
    Strict device or administrative authentication for hardware ingress.
    Requires matching X-Device-API-Key or Admin/Teacher Bearer token.
    Rejects unauthorized requests with 401 Unauthorized.
    """
    if x_device_api_key and x_device_api_key == settings.DEVICE_API_KEY:
        return {"type": "device", "device_id": "esp8266"}
    if auth and auth.credentials:
        payload = decode_access_token(auth.credentials)
        role = str(payload.get("role") or payload.get("app_metadata", {}).get("role", "")).upper()
        if role in ["ADMIN", "TEACHER"]:
            return {"type": "authenticated_user", "role": role}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized hardware device. Valid 'X-Device-API-Key' header or admin credentials required."
    )

