from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.teacher import TeacherModel
from app.models.user import UserModel
from app.core.security import get_password_hash
from app.core.exceptions import EntityNotFoundError, DuplicateEntityError

class TeacherService:
    @staticmethod
    def get_all(
        db: Session,
        department: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[TeacherModel]:
        q = db.query(TeacherModel).filter(TeacherModel.is_active == True)

        if department:
            q = q.filter(TeacherModel.department.ilike(f"%{department}%"))

        if query:
            pattern = f"%{query}%"
            q = q.filter(
                or_(
                    TeacherModel.name.ilike(pattern),
                    TeacherModel.teacher_id.ilike(pattern),
                    TeacherModel.email.ilike(pattern)
                )
            )

        return q.order_by(TeacherModel.id.asc()).all()

    @staticmethod
    def get_by_id(db: Session, teacher_id: int) -> TeacherModel:
        teacher = db.query(TeacherModel).filter(TeacherModel.id == teacher_id).first()
        if not teacher:
            raise EntityNotFoundError("Teacher", teacher_id)
        return teacher

    @staticmethod
    def create(db: Session, data: Dict[str, Any]) -> TeacherModel:
        email = data.get("email", "").strip().lower()
        if db.query(TeacherModel).filter(TeacherModel.email == email).first():
            raise DuplicateEntityError("Teacher", "email", email)

        tid = data.get("teacher_id", "").strip()
        if db.query(TeacherModel).filter(TeacherModel.teacher_id == tid).first():
            raise DuplicateEntityError("Teacher", "teacher_id", tid)

        # Provision UserModel
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            password = data.get("password") or "Teacher@123"
            user = UserModel(
                email=email,
                username=tid,
                full_name=data.get("name", "Faculty Member"),
                hashed_password=get_password_hash(password),
                role="TEACHER",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        teacher = TeacherModel(
            user_id=user.id,
            teacher_id=tid,
            name=data.get("name", "").strip(),
            email=email,
            department=data.get("department", "Computer Science & Engineering"),
            is_active=True
        )
        teacher.assigned_divisions = data.get("assigned_divisions", ["A"])
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        return teacher

    @staticmethod
    def update(db: Session, teacher_id: int, data: Dict[str, Any]) -> TeacherModel:
        teacher = TeacherService.get_by_id(db, teacher_id)

        for field in ["name", "department", "is_active"]:
            if field in data and data[field] is not None:
                setattr(teacher, field, data[field])

        if "assigned_divisions" in data and data["assigned_divisions"] is not None:
            teacher.assigned_divisions = data["assigned_divisions"]

        if "email" in data and data["email"]:
            new_email = data["email"].strip().lower()
            if new_email != teacher.email:
                if db.query(TeacherModel).filter(TeacherModel.email == new_email).first():
                    raise DuplicateEntityError("Teacher", "email", new_email)
                teacher.email = new_email

        db.commit()
        db.refresh(teacher)
        return teacher

    @staticmethod
    def deactivate(db: Session, teacher_id: int) -> TeacherModel:
        teacher = TeacherService.get_by_id(db, teacher_id)
        teacher.is_active = False
        if teacher.user:
            teacher.user.is_active = False
        db.commit()
        db.refresh(teacher)
        return teacher

