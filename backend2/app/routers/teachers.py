from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserModel
from app.schemas.teacher import TeacherCreate, TeacherUpdate, TeacherResponse
from app.services.teacher_service import TeacherService
from app.core.permissions import require_admin, require_teacher

router = APIRouter(prefix="/teachers", tags=["Teachers"])

@router.get("", response_model=List[TeacherResponse], summary="List Faculty")
def list_teachers(
    department: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):
    teachers = TeacherService.get_all(db, department=department, query=q)
    return [
        {
            "id": t.id,
            "teacher_id": t.teacher_id,
            "employee_id": t.teacher_id,
            "name": t.name,
            "full_name": t.name,
            "email": t.email,
            "department": t.department,
            "assigned_divisions": t.assigned_divisions,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in teachers
    ]

@router.post("", response_model=TeacherResponse, summary="Create Faculty Member")
def create_teacher(
    payload: TeacherCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):
    teacher = TeacherService.create(db, payload.model_dump())
    return {
        "id": teacher.id,
        "teacher_id": teacher.teacher_id,
        "employee_id": teacher.teacher_id,
        "name": teacher.name,
        "full_name": teacher.name,
        "email": teacher.email,
        "department": teacher.department,
        "assigned_divisions": teacher.assigned_divisions,
        "is_active": teacher.is_active,
        "created_at": teacher.created_at.isoformat() if teacher.created_at else None
    }

@router.get("/{teacher_id}", response_model=TeacherResponse, summary="Get Faculty Details")
def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)
):
    teacher = TeacherService.get_by_id(db, teacher_id)
    return {
        "id": teacher.id,
        "teacher_id": teacher.teacher_id,
        "employee_id": teacher.teacher_id,
        "name": teacher.name,
        "full_name": teacher.name,
        "email": teacher.email,
        "department": teacher.department,
        "assigned_divisions": teacher.assigned_divisions,
        "is_active": teacher.is_active,
        "created_at": teacher.created_at.isoformat() if teacher.created_at else None
    }

@router.put("/{teacher_id}", response_model=TeacherResponse, summary="Update Faculty Details")
def update_teacher(
    teacher_id: int,
    payload: TeacherUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):
    teacher = TeacherService.update(db, teacher_id, payload.model_dump(exclude_unset=True))
    return {
        "id": teacher.id,
        "teacher_id": teacher.teacher_id,
        "employee_id": teacher.teacher_id,
        "name": teacher.name,
        "full_name": teacher.name,
        "email": teacher.email,
        "department": teacher.department,
        "assigned_divisions": teacher.assigned_divisions,
        "is_active": teacher.is_active,
        "created_at": teacher.created_at.isoformat() if teacher.created_at else None
    }

@router.patch("/{teacher_id}/deactivate", summary="Deactivate Faculty Account")
def deactivate_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):
    TeacherService.deactivate(db, teacher_id)
    return {"status": "success", "message": f"Faculty #{teacher_id} successfully deactivated."}

