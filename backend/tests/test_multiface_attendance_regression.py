import uuid
import math
import numpy as np
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.teacher import TeacherModel
from app.models.student import StudentModel
from app.models.face_embedding import FaceEmbeddingModel
from app.models.daily_checkin import DailyCheckinModel
from app.models.lecture_session import LectureSessionModel
from app.models.lecture_attendance import LectureAttendanceModel
from app.services.face_recognition import FaceRecognitionService
from app.services.verification_engine import VerificationEngine
from app.core.security import create_access_token

# Isolated SQLite in-memory database fixture for regression testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def isolated_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def test_client(isolated_db):
    def override_get_db():
        try:
            yield isolated_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def make_test_vector(dominant_dim: int, val: float = 1.0) -> list[float]:
    """Creates a normalized 512-d vector with energy focused in specific dimension."""
    v = [0.0] * 512
    v[dominant_dim] = val
    # Normalize
    arr = np.array(v, dtype=np.float32)
    norm = np.linalg.norm(arr)
    return (arr / norm).tolist()

def make_similar_vector(base_vector: list[float], similarity: float) -> list[float]:
    """Creates a vector with an exact cosine similarity to base_vector without external random DLLs."""
    v1 = np.array(base_vector, dtype=np.float32)
    v1 = v1 / np.linalg.norm(v1)
    
    # Generate deterministic orthogonal vector
    ortho = np.zeros(512, dtype=np.float32)
    min_dim = int(np.argmin(np.abs(v1)))
    ortho[min_dim] = 1.0
    ortho = ortho - np.dot(ortho, v1) * v1
    ortho = ortho / np.linalg.norm(ortho)
    
    sim_clamped = max(min(similarity, 1.0), -1.0)
    sin_theta = math.sqrt(max(0.0, 1.0 - sim_clamped**2))
    v2 = sim_clamped * v1 + sin_theta * ortho
    return (v2 / np.linalg.norm(v2)).tolist()


# ── SCENARIO 1: One detected, correctly enrolled student ─────────────────────────
def test_scenario_1_single_detected_enrolled_student(test_client, isolated_db):
    """
    Scenario 1: One detected, correctly enrolled student.
    - AI matches student above threshold.
    - Unique match recorded as AI detection.
    - If student tapped RFID, status is PRESENT (RFID_AND_AI).
    """
    teacher = TeacherModel(id=1, teacher_id="TCH-001", name="Prof Test", email="t1@test.edu", password_hash="pw", department="CS", is_active=True)
    student1 = StudentModel(id=101, roll_no="R-101", name="Student One", email="s1@test.edu", department="CS", year="3rd Year", division="A", rfid_uid="RFID:TEST:101", is_active=True)
    isolated_db.add_all([teacher, student1])
    isolated_db.commit()

    v1 = make_test_vector(10)
    enrolled_map = {
        101: {"student": {"id": 101, "name": "Student One", "roll_no": "R-101"}, "embeddings": [v1]}
    }

    rec_service = FaceRecognitionService()
    detected_faces = [{"bbox": [10, 10, 50, 50], "conf": 0.95, "face_crop": np.zeros((50, 50, 3), dtype=np.uint8)}]

    # Mock embedding extraction to return v1
    rec_service.embedder.generate_embedding = lambda crop: v1
    results = rec_service.process_classroom_detections(detected_faces, enrolled_map, threshold=0.70)

    assert len(results["recognized"]) == 1
    assert 101 in results["recognized"]
    assert results["recognized"][101]["similarity"] >= 0.99
    assert len(results["ambiguous"]) == 0
    assert len(results["unknown"]) == 0

    # Cross-verify with RFID check-in
    matrix = VerificationEngine.compute_lecture_verification_matrix(
        division_students=[{"id": 101, "name": "Student One", "roll_no": "R-101"}],
        daily_checked_in_student_ids={101},
        ai_recognized_map={101: results["recognized"][101]["similarity"]},
        auto_mark_absent=False
    )
    assert matrix["verified_present"] == 1
    assert matrix["results"][0]["status"] == "PRESENT"
    assert matrix["results"][0]["verification_source"] == "RFID_AND_AI"


# ── SCENARIO 2: Two detected students with two different valid identities ────────
def test_scenario_2_two_detected_different_valid_identities(test_client, isolated_db):
    """
    Scenario 2: Two detected students with two different valid identities.
    - Face 1 matches Student A, Face 2 matches Student B.
    - Both recognized independently without collision or mutual overwrite.
    """
    v_a = make_test_vector(1)
    v_b = make_test_vector(2)
    enrolled_map = {
        1: {"student": {"id": 1, "name": "Alice", "roll_no": "R-1"}, "embeddings": [v_a]},
        2: {"student": {"id": 2, "name": "Bob", "roll_no": "R-2"}, "embeddings": [v_b]}
    }

    rec_service = FaceRecognitionService()
    detected_faces = [
        {"bbox": [10, 10, 50, 50], "conf": 0.92, "face_crop": np.full((50, 50, 3), 1, dtype=np.uint8)},
        {"bbox": [100, 10, 50, 50], "conf": 0.89, "face_crop": np.full((50, 50, 3), 2, dtype=np.uint8)}
    ]

    def mock_embed(crop):
        val = int(crop[0, 0, 0])
        return v_a if val == 1 else v_b

    rec_service.embedder.generate_embedding = mock_embed
    results = rec_service.process_classroom_detections(detected_faces, enrolled_map, threshold=0.70)

    assert len(results["recognized"]) == 2
    assert 1 in results["recognized"]
    assert 2 in results["recognized"]
    assert results["recognized"][1]["student"]["name"] == "Alice"
    assert results["recognized"][2]["student"]["name"] == "Bob"
    assert len(results["duplicates"]) == 0
    assert len(results["unknown"]) == 0


# ── SCENARIO 3: Two detected faces where only one identity is recognized ──────────
def test_scenario_3_two_detected_one_recognized_one_unknown(test_client, isolated_db):
    """
    Scenario 3: Two detected faces where only one identity is recognized.
    - Face 1 matches Student A (high confidence).
    - Face 2 has low similarity (< 0.70) against all students.
    - Result: Face 1 is recognized, Face 2 is classified as unknown.
    """
    v_a = make_test_vector(5)
    v_random = make_test_vector(50) # Orthogonal vector

    enrolled_map = {
        1: {"student": {"id": 1, "name": "Alice", "roll_no": "R-1"}, "embeddings": [v_a]}
    }

    rec_service = FaceRecognitionService()
    detected_faces = [
        {"bbox": [20, 20, 60, 60], "conf": 0.94, "face_crop": np.full((60, 60, 3), 1, dtype=np.uint8)},
        {"bbox": [200, 20, 60, 60], "conf": 0.85, "face_crop": np.full((60, 60, 3), 9, dtype=np.uint8)}
    ]

    rec_service.embedder.generate_embedding = lambda crop: v_a if int(crop[0, 0, 0]) == 1 else v_random
    results = rec_service.process_classroom_detections(detected_faces, enrolled_map, threshold=0.70)

    assert len(results["recognized"]) == 1
    assert 1 in results["recognized"]
    assert len(results["unknown"]) == 1
    assert results["unknown"][0]["bbox"] == [200, 20, 60, 60]


# ── SCENARIO 4: An unknown face ──────────────────────────────────────────────────
def test_scenario_4_unknown_face():
    """
    Scenario 4: An unknown face.
    - Similarity below configured threshold (0.70).
    - Face marked as unknown, never assigned to an arbitrary student.
    """
    v_enrolled = make_test_vector(10)
    v_intruder = make_similar_vector(v_enrolled, similarity=0.45) # Well below 0.70

    enrolled_map = {
        99: {"student": {"id": 99, "name": "Registered Student", "roll_no": "R-99"}, "embeddings": [v_enrolled]}
    }

    rec_service = FaceRecognitionService()
    match = rec_service.match_face(v_intruder, enrolled_map, threshold=0.70)

    assert match["status"] == "unknown"
    assert match["student"] is None
    assert match["similarity"] < 0.70


# ── SCENARIO 5: Two candidates with ambiguous similarity scores ──────────────────
def test_scenario_5_two_candidates_ambiguous_similarity():
    """
    Scenario 5: Two candidates with ambiguous similarity scores.
    - Candidate 1 similarity: 0.84, Candidate 2 similarity: 0.80.
    - Difference = 0.04 < 0.08 (AMBIGUITY_THRESHOLD).
    - Status must be 'ambiguous', preserving both candidates.
    """
    v_query = make_test_vector(0)
    v_c1 = make_similar_vector(v_query, similarity=0.84)
    v_c2 = make_similar_vector(v_query, similarity=0.80)

    enrolled_map = {
        10: {"student": {"id": 10, "name": "Student 10", "roll_no": "R-10"}, "embeddings": [v_c1]},
        20: {"student": {"id": 20, "name": "Student 20", "roll_no": "R-20"}, "embeddings": [v_c2]}
    }

    rec_service = FaceRecognitionService()
    match = rec_service.match_face(v_query, enrolled_map, threshold=0.70)

    assert match["status"] == "ambiguous"
    assert match["ambiguity_details"] is not None
    candidates = match["ambiguity_details"]["candidates"]
    candidate_ids = {c["student"]["id"] for c in candidates}
    assert 10 in candidate_ids and 20 in candidate_ids
    assert match["ambiguity_details"]["margin"] < 0.08


# ── SCENARIO 6: Ambiguous match resolved by exactly one daily RFID check-in ──────
def test_scenario_6_ambiguous_match_resolved_by_single_rfid():
    """
    Scenario 6: Ambiguous match resolved by exactly one candidate's daily RFID check-in.
    - Two competing candidates (Student 10 at 0.85, Student 20 at 0.82, diff=0.03 < 0.08).
    - Only Student 20 checked in via RFID today.
    - RFID check-in resolves the ambiguity strictly to Student 20.
    """
    v_query = make_test_vector(0)
    v_c1 = make_similar_vector(v_query, similarity=0.85)
    v_c2 = make_similar_vector(v_query, similarity=0.82)

    enrolled_map = {
        10: {"student": {"id": 10, "name": "Student 10", "roll_no": "R-10"}, "embeddings": [v_c1]},
        20: {"student": {"id": 20, "name": "Student 20", "roll_no": "R-20"}, "embeddings": [v_c2]}
    }

    rec_service = FaceRecognitionService()
    detected_faces = [{"bbox": [50, 50, 100, 100], "conf": 0.90, "face_crop": np.zeros((100, 100, 3), dtype=np.uint8)}]
    rec_service.embedder.generate_embedding = lambda crop: v_query

    results = rec_service.process_classroom_detections(detected_faces, enrolled_map, threshold=0.70)
    assert len(results["ambiguous"]) == 1

    # Simulate RFID resolution in router
    daily_checked_in_ids = {20} # Only Student 20 has RFID check-in
    ai_recognized_map = {}

    for amb in results["ambiguous"]:
        candidates = amb["ambiguity_details"]["candidates"]
        rfid_matched = [c for c in candidates if c["student"]["id"] in daily_checked_in_ids]
        assert len(rfid_matched) == 1
        best = rfid_matched[0]
        ai_recognized_map[best["student"]["id"]] = best["similarity"]

    assert 20 in ai_recognized_map
    assert 10 not in ai_recognized_map
    assert ai_recognized_map[20] == pytest.approx(0.82, abs=0.01)


# ── SCENARIO 7: Multiple detections of the same person ────────────────────────────
def test_scenario_7_multiple_detections_same_person():
    """
    Scenario 7: Multiple detections of the same person.
    - Two face bounding boxes in the classroom match Student A.
    - Higher confidence detection is recognized.
    - Second detection is marked as duplicate.
    - Exactly one attendance record persisted; duplicate does not overwrite.
    """
    v_a = make_test_vector(7)
    enrolled_map = {
        1: {"student": {"id": 1, "name": "Alice", "roll_no": "R-1"}, "embeddings": [v_a]}
    }

    rec_service = FaceRecognitionService()
    # Detection 1: similarity 0.95. Detection 2: similarity 0.88
    v_crop1 = make_similar_vector(v_a, 0.95)
    v_crop2 = make_similar_vector(v_a, 0.88)

    detected_faces = [
        {"bbox": [10, 10, 50, 50], "conf": 0.91, "face_crop": np.full((50, 50, 3), 1, dtype=np.uint8)},
        {"bbox": [120, 10, 50, 50], "conf": 0.84, "face_crop": np.full((50, 50, 3), 2, dtype=np.uint8)}
    ]

    rec_service.embedder.generate_embedding = lambda crop: v_crop1 if int(crop[0, 0, 0]) == 1 else v_crop2
    results = rec_service.process_classroom_detections(detected_faces, enrolled_map, threshold=0.70)

    assert len(results["recognized"]) == 1
    assert 1 in results["recognized"]
    assert results["recognized"][1]["similarity"] == pytest.approx(0.95, abs=0.01)
    assert len(results["duplicates"]) == 1
    assert results["duplicates"][0]["match_status"] == "duplicate"


# ── SCENARIO 8: Face embedding failure for the second face ───────────────────────
def test_scenario_8_face_embedding_failure_second_face():
    """
    Scenario 8: Face embedding failure for the second face.
    - Face 1 generates valid embedding and matches Student A.
    - Face 2 causes an exception in embedding generation (or returns None).
    - Pipeline must not crash; Face 1 is recognized, Face 2 recorded as unknown/failed.
    """
    v_a = make_test_vector(3)
    enrolled_map = {
        1: {"student": {"id": 1, "name": "Alice", "roll_no": "R-1"}, "embeddings": [v_a]}
    }

    rec_service = FaceRecognitionService()
    detected_faces = [
        {"bbox": [10, 10, 50, 50], "conf": 0.95, "face_crop": np.full((50, 50, 3), 1, dtype=np.uint8)},
        {"bbox": [80, 10, 50, 50], "conf": 0.90, "face_crop": np.full((50, 50, 3), 2, dtype=np.uint8)}
    ]

    def mock_embed_with_failure(crop):
        if int(crop[0, 0, 0]) == 2:
            raise RuntimeError("InsightFace ONNX runtime memory error")
        return v_a

    rec_service.embedder.generate_embedding = mock_embed_with_failure
    results = rec_service.process_classroom_detections(detected_faces, enrolled_map, threshold=0.70)

    assert len(results["recognized"]) == 1
    assert 1 in results["recognized"]
    assert len(results["unknown"]) == 1
    assert results["unknown"][0]["bbox"] == [80, 10, 50, 50]


# ── SCENARIO 9: Correct dashboard counts after attendance persistence ────────────
def test_scenario_9_correct_dashboard_counts_after_persistence(test_client, isolated_db):
    """
    Scenario 9: Correct dashboard counts after attendance persistence.
    - Roster has 10 students.
    - 2 Confirmed Present (RFID + AI).
    - 2 Flagged for Review (1 AI only, 1 RFID only).
    - 6 Undetected students remain PENDING (not arbitrarily marked absent).
    - Mutually exclusive & exhaustive: Present (2) + Flagged (2) + Pending (6) = 10.
    """
    # Create teacher and 10 students
    teacher = TeacherModel(id=1, teacher_id="TCH-001", name="Prof Test", email="prof@test.edu", password_hash="pw", department="CS", is_active=True)
    isolated_db.add(teacher)
    
    students = []
    for i in range(1, 11):
        st = StudentModel(id=i, roll_no=f"R-{i:02d}", name=f"Student {i}", email=f"s{i}@test.edu", department="CS", year="3rd Year", division="A", rfid_uid=f"RFID:TEST:{i}", is_active=True)
        students.append(st)
        isolated_db.add(st)
    
    lecture = LectureSessionModel(id=10, teacher_id=1, subject="Data Structures", division="A", date=date.today(), status="ACTIVE")
    isolated_db.add(lecture)
    isolated_db.commit()

    # Students 1 & 2: RFID + AI -> PRESENT
    # Student 3: AI only -> FLAGGED
    # Student 4: RFID only -> FLAGGED
    # Students 5-10: Neither -> PENDING
    division_dicts = [{"id": s.id, "name": s.name, "roll_no": s.roll_no, "department": s.department, "division": s.division} for s in students]
    matrix = VerificationEngine.compute_lecture_verification_matrix(
        division_students=division_dicts,
        daily_checked_in_student_ids={1, 2, 4},
        ai_recognized_map={1: 0.95, 2: 0.92, 3: 0.88},
        auto_mark_absent=False
    )

    assert matrix["verified_present"] == 2
    assert matrix["ai_only"] == 1
    assert matrix["rfid_only"] == 1
    assert matrix["pending"] == 6
    assert matrix["absent"] == 0

    # Persist in DB
    for res in matrix["results"]:
        isolated_db.add(LectureAttendanceModel(
            lecture_session_id=lecture.id,
            student_id=res["student_id"],
            status=res["status"],
            verification_source=res["verification_source"],
            ai_confidence=res["ai_confidence"],
            rfid_checked_in=res["rfid_checked_in"],
            ai_detected=res["ai_detected"]
        ))
    isolated_db.commit()

    atts = isolated_db.query(LectureAttendanceModel).filter(LectureAttendanceModel.lecture_session_id == 10).all()
    present_cnt = sum(1 for a in atts if a.status == "PRESENT")
    flagged_cnt = sum(1 for a in atts if a.status == "FLAGGED")
    pending_cnt = sum(1 for a in atts if a.status == "PENDING")
    absent_cnt = sum(1 for a in atts if a.status == "ABSENT")

    assert len(atts) == 10
    assert present_cnt == 2
    assert flagged_cnt == 2
    assert pending_cnt == 6
    assert absent_cnt == 0
    assert present_cnt + flagged_cnt + pending_cnt + absent_cnt == len(atts)


# ── SCENARIO 10: Teacher review and attendance finalization ───────────────────────
def test_scenario_10_teacher_review_and_finalization(test_client, isolated_db):
    """
    Scenario 10: Teacher review and attendance finalization.
    - Teacher resolves flagged student (Confirms Student 3 present).
    - Teacher finalizes lecture session.
    - All remaining PENDING students transition to ABSENT.
    - All records locked as immutable (finalized=True).
    - Present + Flagged + Absent = Total Enrolled.
    """
    teacher = TeacherModel(id=2, teacher_id="TCH-002", name="Prof Turing", email="turing@test.edu", password_hash="pw", department="CS", is_active=True)
    isolated_db.add(teacher)
    
    students = []
    for i in range(1, 6):
        st = StudentModel(id=i, roll_no=f"R-{i:02d}", name=f"Student {i}", email=f"s{i}@test.edu", department="CS", year="3rd Year", division="A", rfid_uid=f"RFID:TEST:{i}", is_active=True)
        students.append(st)
        isolated_db.add(st)

    lecture = LectureSessionModel(id=20, teacher_id=2, subject="Algorithms", division="A", date=date.today(), status="ACTIVE")
    isolated_db.add(lecture)
    isolated_db.commit()

    token = create_access_token({"sub": "2", "role": "TEACHER"})
    headers = {"Authorization": f"Bearer {token}"}

    # Initial attendance state:
    # Student 1: PRESENT
    # Student 2: FLAGGED (AI only)
    # Student 3, 4, 5: PENDING
    initial_records = [
        LectureAttendanceModel(lecture_session_id=20, student_id=1, status="PRESENT", verification_source="RFID_AND_AI"),
        LectureAttendanceModel(lecture_session_id=20, student_id=2, status="FLAGGED", verification_source="AI_ONLY"),
        LectureAttendanceModel(lecture_session_id=20, student_id=3, status="PENDING", verification_source="UNVERIFIED"),
        LectureAttendanceModel(lecture_session_id=20, student_id=4, status="PENDING", verification_source="UNVERIFIED"),
        LectureAttendanceModel(lecture_session_id=20, student_id=5, status="PENDING", verification_source="UNVERIFIED"),
    ]
    isolated_db.add_all(initial_records)
    isolated_db.commit()

    # 1. Teacher confirms Student 2 present via flag resolution
    res_flag = test_client.post(
        "/api/lectures/20/resolve-flag",
        json={"student_id": 2, "action": "CONFIRM_PRESENT"},
        headers=headers
    )
    assert res_flag.status_code == 200
    assert res_flag.json()["status"] == "PRESENT"

    # 2. Teacher finalizes lecture session
    res_fin = test_client.post("/api/lectures/20/finalize", headers=headers)
    assert res_fin.status_code == 200
    assert res_fin.json()["status"] == "FINALIZED"

    # 3. Verify in database
    attendances = isolated_db.query(LectureAttendanceModel).filter(LectureAttendanceModel.lecture_session_id == 20).all()
    assert len(attendances) == 5
    for att in attendances:
        assert att.finalized is True

    att_map = {a.student_id: a for a in attendances}
    assert att_map[1].status == "PRESENT"
    assert att_map[2].status == "PRESENT"
    assert att_map[2].verification_source == "TEACHER_CONFIRMED"
    # PENDING students must have transitioned to ABSENT upon finalization
    assert att_map[3].status == "ABSENT"
    assert att_map[3].verification_source == "FINALIZED_ABSENT"
    assert att_map[4].status == "ABSENT"
    assert att_map[5].status == "ABSENT"

    present_count = sum(1 for a in attendances if a.status == "PRESENT")
    flagged_count = sum(1 for a in attendances if a.status == "FLAGGED")
    absent_count = sum(1 for a in attendances if a.status == "ABSENT")

    assert present_count == 2
    assert flagged_count == 0
    assert absent_count == 3
    assert present_count + flagged_count + absent_count == 5
