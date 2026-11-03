from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.class_division import ClassDivisionModel
from app.schemas.class_division import ClassDivisionCreate, ClassDivisionResponse
from app.services.dashboard_service import DashboardService
from app.core.permissions import require_admin, require_teacher

router = APIRouter(tags=["Academic Portal & Analytics"])

@router.get("/classes", response_model=List[ClassDivisionResponse], summary="List Academic Classes and Divisions")
def list_classes(db: Session = Depends(get_db)):
    divisions = db.query(ClassDivisionModel).all()
    if not divisions:
        # Seed default academic divisions
        div_a = ClassDivisionModel(
            name="A",
            code="CSE-3Y-A",
            academic_year="2026-2027",
            semester="5",
            department="Computer Science & Engineering",
            total_students=60,
            class_teacher="Dr. Sharma",
            is_active=True
        )
        div_b = ClassDivisionModel(
            name="B",
            code="CSE-3Y-B",
            academic_year="2026-2027",
            semester="5",
            department="Computer Science & Engineering",
            total_students=60,
            class_teacher="Prof. Patil",
            is_active=True
        )
        db.add_all([div_a, div_b])
        db.commit()
        divisions = [div_a, div_b]

    return [
        {
            "id": d.id,
            "name": d.name,
            "code": d.code or f"DIV-{d.name}",
            "academic_year": d.academic_year,
            "semester": d.semester,
            "department": d.department,
            "total_students": d.total_students,
            "class_teacher": d.class_teacher,
            "is_active": d.is_active
        }
        for d in divisions
    ]

@router.post("/classes", response_model=ClassDivisionResponse, summary="Create Class / Division")
def create_class(
    payload: ClassDivisionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    div = ClassDivisionModel(
        name=payload.name,
        code=payload.code or f"DIV-{payload.name}",
        academic_year=payload.academic_year or "2026-2027",
        semester=payload.semester or "5",
        department=payload.department or "Computer Science & Engineering",
        class_teacher=payload.class_teacher,
        is_active=True
    )
    db.add(div)
    db.commit()
    db.refresh(div)
    return {
        "id": div.id,
        "name": div.name,
        "code": div.code,
        "academic_year": div.academic_year,
        "semester": div.semester,
        "department": div.department,
        "total_students": div.total_students,
        "class_teacher": div.class_teacher,
        "is_active": div.is_active
    }

@router.get("/classes/{class_id}", response_model=ClassDivisionResponse, summary="Get Division Details")
def get_class(class_id: int, db: Session = Depends(get_db)):
    div = db.query(ClassDivisionModel).filter(ClassDivisionModel.id == class_id).first()
    if not div:
        from app.core.exceptions import EntityNotFoundError
        raise EntityNotFoundError("Class Division", class_id)
    return {
        "id": div.id,
        "name": div.name,
        "code": div.code or f"DIV-{div.name}",
        "academic_year": div.academic_year,
        "semester": div.semester,
        "department": div.department,
        "total_students": div.total_students,
        "class_teacher": div.class_teacher,
        "is_active": div.is_active
    }

@router.get("/admin/stats", summary="Get Institutional Admin KPI Statistics")
def get_admin_stats(db: Session = Depends(get_db)):
    return DashboardService.get_admin_stats(db)

@router.get("/parent/{parent_id}/overview", summary="Get Parent Child Overview")
def get_parent_overview(parent_id: int, db: Session = Depends(get_db)):
    return DashboardService.get_parent_child_overview(db, parent_id)

