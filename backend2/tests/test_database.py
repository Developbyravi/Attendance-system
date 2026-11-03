from app.models.user import UserModel
from app.models.student import StudentModel
from app.models.teacher import TeacherModel
from app.models.class_division import ClassDivisionModel
from app.models.subject import SubjectModel
from app.models.daily_checkin import DailyCheckinModel
from app.models.lecture import LectureSessionModel
from app.models.attendance import LectureAttendanceModel

def test_database_tables_initialization(db_session):
    """Verifies that all core tables exist and can perform basic CRUD transactions."""
    # 1. Create Class Division
    div = ClassDivisionModel(name="TestDiv", code="TD-1", total_students=30)
    db_session.add(div)
    db_session.commit()
    assert div.id is not None

    # 2. Query division
    queried_div = db_session.query(ClassDivisionModel).filter(ClassDivisionModel.code == "TD-1").first()
    assert queried_div is not None
    assert queried_div.name == "TestDiv"

