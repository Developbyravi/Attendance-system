import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend2 is on Python path
backend2_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend2_dir not in sys.path:
    sys.path.insert(0, backend2_dir)

# Override environment for tests
os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///./smartattend_test.db"

from app.database import Base, get_db
from app.main import app
from app.models.user import UserModel
from app.models.teacher import TeacherModel
from app.models.student import StudentModel
from app.models.class_division import ClassDivisionModel
from app.models.subject import SubjectModel
from app.core.security import get_password_hash, create_access_token

TEST_DB_URL = "sqlite:///./smartattend_test.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    db_file = os.path.join(backend2_dir, "smartattend_test.db")
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

@pytest.fixture(autouse=True)
def clean_rfid_sessions():
    from app.services.rfid_service import ACTIVE_ASSIGNMENT_SESSIONS
    ACTIVE_ASSIGNMENT_SESSIONS.clear()
    yield
    ACTIVE_ASSIGNMENT_SESSIONS.clear()

@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def admin_token(db_session):
    admin = db_session.query(UserModel).filter(UserModel.email == "test_admin@smartattend.edu").first()
    if not admin:
        admin = UserModel(
            email="test_admin@smartattend.edu",
            username="admin_test",
            full_name="Admin Test",
            hashed_password=get_password_hash("Admin@123"),
            role="ADMIN",
            is_active=True
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)

    return create_access_token(data={"sub": admin.email, "user_id": admin.id, "role": "ADMIN", "email": admin.email})

@pytest.fixture
def teacher_token(db_session):
    teacher_user = db_session.query(UserModel).filter(UserModel.email == "test_teacher@smartattend.edu").first()
    if not teacher_user:
        teacher_user = UserModel(
            email="test_teacher@smartattend.edu",
            username="TCH-TEST",
            full_name="Teacher Test",
            hashed_password=get_password_hash("Teacher@123"),
            role="TEACHER",
            is_active=True
        )
        db_session.add(teacher_user)
        db_session.commit()
        db_session.refresh(teacher_user)

    teacher = db_session.query(TeacherModel).filter(TeacherModel.user_id == teacher_user.id).first()
    if not teacher:
        teacher = TeacherModel(
            user_id=teacher_user.id,
            teacher_id="TCH-TEST",
            name="Teacher Test",
            email="test_teacher@smartattend.edu",
            department="Computer Science & Engineering",
            is_active=True
        )
        teacher.assigned_divisions = ["A", "B"]
        db_session.add(teacher)
        db_session.commit()

    return create_access_token(data={"sub": teacher_user.email, "user_id": teacher_user.id, "role": "TEACHER", "email": teacher_user.email})

@pytest.fixture
def student_token(db_session):
    student_user = db_session.query(UserModel).filter(UserModel.email == "test_student@smartattend.edu").first()
    if not student_user:
        student_user = UserModel(
            email="test_student@smartattend.edu",
            username="101",
            full_name="Student Test",
            hashed_password=get_password_hash("Student@123"),
            role="STUDENT",
            is_active=True
        )
        db_session.add(student_user)
        db_session.commit()
        db_session.refresh(student_user)

    student = db_session.query(StudentModel).filter(StudentModel.user_id == student_user.id).first()
    if not student:
        student = StudentModel(
            user_id=student_user.id,
            roll_no="101",
            name="Student Test",
            email="test_student@smartattend.edu",
            department="Computer Science & Engineering",
            year="3rd Year",
            division="A",
            rfid_uid="TEST-UID-101",
            face_enrolled=True,
            is_active=True
        )
        db_session.add(student)
        db_session.commit()

    return create_access_token(data={"sub": student_user.email, "user_id": student_user.id, "role": "STUDENT", "email": student_user.email})

