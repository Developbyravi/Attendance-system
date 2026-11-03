import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, init_db
from app.models.user import UserModel
from app.models.teacher import TeacherModel
from app.models.student import StudentModel
from app.models.class_division import ClassDivisionModel
from app.models.subject import SubjectModel
from app.models.attendance import DeviceModel
from app.core.security import get_password_hash

def seed_demo_data():
    print("Initializing DB tables...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Admin
        admin = db.query(UserModel).filter(UserModel.email == "admin@smartattend.edu").first()
        if not admin:
            admin = UserModel(
                email="admin@smartattend.edu",
                username="admin",
                full_name="System Administrator",
                hashed_password=get_password_hash("Admin@123"),
                role="ADMIN",
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print("Seeded Admin: admin@smartattend.edu / Admin@123")

        # 2. Division A & B
        div_a = db.query(ClassDivisionModel).filter(ClassDivisionModel.name == "A").first()
        if not div_a:
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
            db.add(div_a)

        div_b = db.query(ClassDivisionModel).filter(ClassDivisionModel.name == "B").first()
        if not div_b:
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
            db.add(div_b)
        db.commit()

        # 3. Subject
        subj = db.query(SubjectModel).filter(SubjectModel.name == "Deep Learning").first()
        if not subj:
            subj = SubjectModel(
                name="Deep Learning",
                code="CS-501",
                department="Computer Science & Engineering",
                semester="5"
            )
            db.add(subj)
            db.commit()

        # 4. Teacher
        teacher_user = db.query(UserModel).filter(UserModel.email == "teacher@smartattend.edu").first()
        if not teacher_user:
            teacher_user = UserModel(
                email="teacher@smartattend.edu",
                username="TCH-001",
                full_name="Prof. Sharma",
                hashed_password=get_password_hash("Teacher@123"),
                role="TEACHER",
                is_active=True
            )
            db.add(teacher_user)
            db.commit()
            db.refresh(teacher_user)

            teacher = TeacherModel(
                user_id=teacher_user.id,
                teacher_id="TCH-001",
                name="Prof. Sharma",
                email="teacher@smartattend.edu",
                department="Computer Science & Engineering",
                is_active=True
            )
            teacher.assigned_divisions = ["A", "B"]
            db.add(teacher)
            db.commit()
            print("Seeded Teacher: teacher@smartattend.edu / Teacher@123")

        # 5. Device
        dev = db.query(DeviceModel).filter(DeviceModel.device_id == "GATE-READER-01").first()
        if not dev:
            dev = DeviceModel(
                device_id="GATE-READER-01",
                device_name="Main Campus RFID Gate",
                location="Main Gate A",
                status="online",
                firmware_version="v2.1.0-esp8266"
            )
            db.add(dev)
            db.commit()

        # 6. Seed Student Ravi Khile (Roll 10, Div A)
        ravi_user = db.query(UserModel).filter(UserModel.email == "khileravi207@gmail.com").first()
        if not ravi_user:
            ravi_user = UserModel(
                email="khileravi207@gmail.com",
                username="10",
                full_name="Ravi Khile",
                hashed_password=get_password_hash("Student@123"),
                role="STUDENT",
                is_active=True
            )
            db.add(ravi_user)
            db.commit()
            db.refresh(ravi_user)

        ravi_student = db.query(StudentModel).filter(StudentModel.roll_no == "10").first()
        if not ravi_student:
            ravi_student = StudentModel(
                user_id=ravi_user.id,
                roll_no="10",
                name="Ravi Khile",
                email="khileravi207@gmail.com",
                department="Computer Science & Engineering",
                year="3rd Year",
                division="A",
                rfid_uid="4847B047",
                face_enrolled=True,
                is_active=True
            )
            db.add(ravi_student)
            db.commit()
            db.refresh(ravi_student)
            print("Seeded Student: Ravi Khile (Roll 10, Div A, RFID 4847B047)")

        print("Demo seed data completed successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()

