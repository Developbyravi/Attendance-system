import uuid
import cv2
import numpy as np
import pytest
from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.student import StudentModel
from app.models.teacher import TeacherModel
from app.models.lecture_session import LectureSessionModel
from app.models.lecture_attendance import LectureAttendanceModel
from app.models.daily_checkin import DailyCheckinModel
from app.services.face_recognition import get_face_recognition_service
from app.core.security import create_access_token

client = TestClient(app)

def create_sample_image_bytes(w=300, h=300) -> bytes:
    img = np.full((h, w, 3), 160, dtype=np.uint8)
    # Draw simple shapes
    cv2.circle(img, (w // 2, h // 2), 60, (220, 200, 180), -1)
    _, encoded = cv2.imencode(".jpg", img)
    return encoded.tobytes()

@pytest.fixture
def test_db():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def registered_teacher(test_db):
    uid = uuid.uuid4().hex[:6]
    teacher = TeacherModel(
        teacher_id=f"TCH-{uid}",
        name=f"Prof. {uid}",
        email=f"teacher_{uid}@smartattend.edu",
        department="Computer Science",
        password_hash="hashed_pw_test",
        is_active=True
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    token = create_access_token({"sub": str(teacher.id), "role": "TEACHER"})
    return {"teacher": teacher, "token": token, "headers": {"Authorization": f"Bearer {token}"}}

@pytest.fixture
def registered_student_a(test_db):
    uid = uuid.uuid4().hex[:6].upper()
    student = StudentModel(
        roll_no=f"STU-A-{uid}",
        name=f"Student A {uid}",
        email=f"student_a_{uid.lower()}_{uuid.uuid4().hex[:4]}@smartattend.edu",
        department="AI & ML",
        year="3rd Year",
        division="A",
        rfid_uid=f"RFID:A:{uid}:{uuid.uuid4().hex[:4]}",
        password_hash="hashed_pw_test",
        is_active=True
    )
    test_db.add(student)
    test_db.commit()
    test_db.refresh(student)
    token = create_access_token({"sub": str(student.id), "role": "STUDENT"})
    return {"student": student, "token": token, "headers": {"Authorization": f"Bearer {token}"}}

@pytest.fixture
def registered_student_b(test_db):
    uid = uuid.uuid4().hex[:6].upper()
    student = StudentModel(
        roll_no=f"STU-B-{uid}",
        name=f"Student B {uid}",
        email=f"student_b_{uid.lower()}_{uuid.uuid4().hex[:4]}@smartattend.edu",
        department="AI & ML",
        year="3rd Year",
        division="B",
        rfid_uid=f"RFID:B:{uid}:{uuid.uuid4().hex[:4]}",
        password_hash="hashed_pw_test",
        is_active=True
    )
    test_db.add(student)
    test_db.commit()
    test_db.refresh(student)
    token = create_access_token({"sub": str(student.id), "role": "STUDENT"})
    return {"student": student, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


# ── FEATURE 1 TESTS: STUDENT LIVE FACE ENROLLMENT ──

def test_student_self_face_enrollment_camera_capture(registered_student_a, monkeypatch):
    """Student captures live camera photo and self-enrolls with exactly 1 face."""
    headers = registered_student_a["headers"]
    
    # Mock detector to find exactly 1 face
    class MockSingleFaceDetector:
        def detect_faces(self, img):
            return [(40, 40, 100, 100)]

    monkeypatch.setattr("app.services.image_processor.get_face_detector", lambda: MockSingleFaceDetector())

    img_bytes = create_sample_image_bytes()
    res = client.post(
        "/api/student/me/face-enroll",
        headers=headers,
        files={"file": ("camera_snap.jpg", img_bytes, "image/jpeg")}
    )

    assert res.status_code == 200
    data = res.json()
    assert data["student_id"] == registered_student_a["student"].id
    assert data["faces_detected"] == 1
    assert data["successful_embeddings"] == 1
    assert data["status"] == "enrolled"


def test_face_enrollment_zero_faces_rejection(registered_student_a, monkeypatch):
    """Enrollment must reject images when zero faces are detected."""
    headers = registered_student_a["headers"]

    class MockEmptyDetector:
        def detect_faces(self, img):
            return []

    monkeypatch.setattr("app.services.image_processor.get_face_detector", lambda: MockEmptyDetector())

    img_bytes = create_sample_image_bytes()
    res = client.post(
        "/api/student/me/face-enroll",
        headers=headers,
        files={"file": ("camera_empty.jpg", img_bytes, "image/jpeg")}
    )

    assert res.status_code == 400
    assert "No face detected" in res.json()["detail"]


def test_face_enrollment_multiple_faces_rejection(registered_student_a, monkeypatch):
    """Enrollment must reject single-student images containing multiple faces."""
    headers = registered_student_a["headers"]

    class MockMultiDetector:
        def detect_faces(self, img):
            return [(20, 20, 60, 60), (120, 120, 60, 60)]

    monkeypatch.setattr("app.services.image_processor.get_face_detector", lambda: MockMultiDetector())

    img_bytes = create_sample_image_bytes()
    res = client.post(
        "/api/student/me/face-enroll",
        headers=headers,
        files={"file": ("camera_multi.jpg", img_bytes, "image/jpeg")}
    )

    assert res.status_code == 400
    assert "Multiple faces detected (2)" in res.json()["detail"]


def test_face_enrollment_invalid_upload_security(registered_student_a):
    """Uploads with invalid extensions or non-image content are securely rejected."""
    headers = registered_student_a["headers"]

    res = client.post(
        "/api/student/me/face-enroll",
        headers=headers,
        files={"file": ("malicious_script.txt", b"not an image file content", "text/plain")}
    )
    assert res.status_code == 400


def test_prevent_cross_student_enrollment_tampering(registered_student_a, registered_student_b):
    """Student A is forbidden from enrolling or replacing Student B's face data."""
    headers_a = registered_student_a["headers"]
    student_b_id = registered_student_b["student"].id

    img_bytes = create_sample_image_bytes()
    res = client.post(
        f"/api/students/{student_b_id}/face-enroll",
        headers=headers_a,
        files={"file": ("hacked.jpg", img_bytes, "image/jpeg")}
    )

    assert res.status_code == 403
    assert "enroll biometric face data for your own student account" in res.json()["detail"]


# ── FEATURE 2, 3, 4: LIVE CLASSROOM MULTI-FACE DETECTION & OVERLAYS ──

def test_classroom_verification_multi_face_and_overlay(registered_teacher, registered_student_a, monkeypatch):
    """Classroom photo verification detects multiple faces, returns detected_boxes and overlay_image_url."""
    headers = registered_teacher["headers"]
    student = registered_student_a["student"]

    # 1. Create lecture for Division A
    lec_res = client.post(
        "/api/lectures",
        json={"subject": "Deep Learning", "division": "A"},
        headers=headers
    )
    assert lec_res.status_code == 201
    lec_id = lec_res.json()["id"]

    # 2. Mock detector to return 3 face boxes (Student A, Unknown Face, Another Face)
    class MockClassroomDetector:
        def detect_faces(self, img):
            return [
                (40, 40, 70, 70),
                (140, 40, 70, 70),
                (240, 40, 70, 70)
            ]

    # 3. Mock matcher
    call_idx = 0
    rec_service = get_face_recognition_service()
    def mock_match(query_vec, enrolled_map, threshold=0.70):
        nonlocal call_idx
        call_idx += 1
        if call_idx == 1:
            return {
                "status": "recognized",
                "confidence": 0.94,
                "student": {"id": student.id, "name": student.name, "roll_no": student.roll_no, "department": student.department}
            }
        else:
            return {
                "status": "unknown",
                "confidence": 0.35,
                "student": None
            }

    monkeypatch.setattr("app.routers.lectures.get_face_detector", lambda: MockClassroomDetector())
    monkeypatch.setattr(rec_service, "match_face", mock_match)

    img_bytes = create_sample_image_bytes(400, 300)
    res = client.post(
        f"/api/lectures/{lec_id}/photo",
        headers=headers,
        files={"file": ("classroom_live.jpg", img_bytes, "image/jpeg")}
    )

    assert res.status_code == 200
    data = res.json()
    assert data["lecture_id"] == lec_id
    assert data["detected_faces"] == 3
    assert len(data["detected_boxes"]) == 3

    # Check boxes have required schema fields
    box0 = data["detected_boxes"][0]
    assert "bbox" in box0
    assert "detector_confidence" in box0
    assert "match_status" in box0
    assert box0["match_status"] == "recognized"
    assert box0["student_id"] == student.id

    # Check unknown box
    box1 = data["detected_boxes"][1]
    assert box1["match_status"] == "unknown"
    assert box1["student_id"] is None

    # Check overlay_image_url field
    assert "overlay_image_url" in data


def test_classroom_duplicate_suppression_and_unknowns(registered_teacher, registered_student_a, monkeypatch):
    """If same student detected in multiple boxes, student is counted once and second box is duplicate."""
    headers = registered_teacher["headers"]
    student = registered_student_a["student"]

    lec_res = client.post(
        "/api/lectures",
        json={"subject": "Computer Vision", "division": "A"},
        headers=headers
    )
    lec_id = lec_res.json()["id"]

    class MockDupDetector:
        def detect_faces(self, img):
            return [(30, 30, 60, 60), (120, 30, 60, 60)]

    rec_service = get_face_recognition_service()
    # Both detections match the same student
    def mock_match(query_vec, enrolled_map, threshold=0.70):
        return {
            "status": "recognized",
            "confidence": 0.91,
            "student": {"id": student.id, "name": student.name, "roll_no": student.roll_no, "department": student.department}
        }

    monkeypatch.setattr("app.routers.lectures.get_face_detector", lambda: MockDupDetector())
    monkeypatch.setattr(rec_service, "match_face", mock_match)

    img_bytes = create_sample_image_bytes()
    res = client.post(
        f"/api/lectures/{lec_id}/photo",
        headers=headers,
        files={"file": ("classroom_dup.jpg", img_bytes, "image/jpeg")}
    )

    assert res.status_code == 200
    data = res.json()
    # Unique AI detected student count is exactly 1 (not 2)
    assert data["ai_detected_count"] == 1
    # Check boxes include recognized and duplicate
    statuses = [b["match_status"] for b in data["detected_boxes"]]
    assert "recognized" in statuses
    assert "duplicate" in statuses


# ── FEATURE 5: RFID + ATTENDANCE DECISION RULES ──

def test_rfid_cross_verification_decision_matrix(registered_teacher, test_db, monkeypatch):
    """
    Evaluates attendance decision matrix:
    1. Student 1: Daily RFID + Confident AI Match -> PRESENT
    2. Student 2: Daily RFID only (not seen by camera) -> FLAGGED
    3. Student 3: Confident AI Match only (no daily RFID) -> FLAGGED
    4. Student 4: Neither -> ABSENT
    """
    headers = registered_teacher["headers"]
    today_date = date.today()

    # Create 4 students in Division C
    students = []
    matrix_run_id = uuid.uuid4().hex[:6]
    for i in range(1, 5):
        s = StudentModel(
            roll_no=f"DEC-C-{i}-{matrix_run_id}",
            name=f"Decision Student {i}",
            email=f"dec_student_{i}_{matrix_run_id}@test.edu",
            department="AI",
            year="3rd Year",
            division="C",
            rfid_uid=f"RFID:DEC:{i}:{matrix_run_id}",
            password_hash="pw",
            is_active=True
        )
        test_db.add(s)
        students.append(s)
    test_db.commit()
    for s in students:
        test_db.refresh(s)

    s1, s2, s3, s4 = students

    # Record daily RFID check-in for s1 and s2
    test_db.add(DailyCheckinModel(student_id=s1.id, rfid_uid=s1.rfid_uid, date=today_date))
    test_db.add(DailyCheckinModel(student_id=s2.id, rfid_uid=s2.rfid_uid, date=today_date))
    test_db.commit()

    # Create lecture for Division C
    lec_res = client.post(
        "/api/lectures",
        json={"subject": "Decision Matrix 101", "division": "C", "date": today_date.isoformat()},
        headers=headers
    )
    lec_id = lec_res.json()["id"]

    # Mock detector to find 2 faces (matching s1 and s3)
    class MockMatrixDetector:
        def detect_faces(self, img):
            return [(20, 20, 50, 50), (100, 20, 50, 50)]

    call_count = 0
    rec_service = get_face_recognition_service()
    def mock_match(query_vec, enrolled_map, threshold=0.70):
        nonlocal call_count
        call_count += 1
        matched_student = s1 if call_count == 1 else s3
        return {
            "status": "recognized",
            "confidence": 0.95,
            "student": {"id": matched_student.id, "name": matched_student.name, "roll_no": matched_student.roll_no, "department": matched_student.department}
        }

    monkeypatch.setattr("app.routers.lectures.get_face_detector", lambda: MockMatrixDetector())
    monkeypatch.setattr(rec_service, "match_face", mock_match)

    res = client.post(
        f"/api/lectures/{lec_id}/photo",
        headers=headers,
        files={"file": ("matrix.jpg", create_sample_image_bytes(), "image/jpeg")}
    )

    assert res.status_code == 200
    data = res.json()
    att_by_student = {a["student_id"]: a for a in data["attendances"]}

    # Rule 1: RFID + AI -> PRESENT
    assert att_by_student[s1.id]["status"] == "PRESENT"
    assert att_by_student[s1.id]["verification_source"] == "RFID_AND_AI"

    # Rule 2: RFID only -> FLAGGED
    assert att_by_student[s2.id]["status"] == "FLAGGED"
    assert att_by_student[s2.id]["verification_source"] == "RFID_ONLY"

    # Rule 3: AI only -> FLAGGED
    assert att_by_student[s3.id]["status"] == "FLAGGED"
    assert att_by_student[s3.id]["verification_source"] == "AI_ONLY"

    # Rule 4: Neither -> ABSENT or PENDING per configured attendance workflow
    assert att_by_student[s4.id]["status"] in ["ABSENT", "PENDING"]


def test_teacher_flag_resolution_and_finalization(registered_teacher, registered_student_a, test_db):
    """Tests teacher resolving student flag and finalizing lecture with immutability enforcement."""
    headers = registered_teacher["headers"]
    student = registered_student_a["student"]

    # Create lecture
    lec_res = client.post(
        "/api/lectures",
        json={"subject": "Robotics", "division": "A"},
        headers=headers
    )
    lec_id = lec_res.json()["id"]

    # Add initial FLAGGED attendance
    att = LectureAttendanceModel(
        lecture_session_id=lec_id,
        student_id=student.id,
        status="FLAGGED",
        verification_source="RFID_ONLY",
        rfid_checked_in=True,
        ai_detected=False,
        finalized=False
    )
    test_db.add(att)
    test_db.commit()

    # Teacher confirms PRESENT
    resolve_res = client.post(
        f"/api/lectures/{lec_id}/resolve-flag",
        json={"student_id": student.id, "action": "CONFIRM_PRESENT"},
        headers=headers
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "PRESENT"
    assert resolve_res.json()["verification_source"] == "TEACHER_CONFIRMED"

    # Teacher finalizes lecture session
    finalize_res = client.post(
        f"/api/lectures/{lec_id}/finalize",
        headers=headers
    )
    assert finalize_res.status_code == 200
    assert finalize_res.json()["status"] == "FINALIZED"

    # Verify immutability: Cannot upload photos after finalization
    photo_res = client.post(
        f"/api/lectures/{lec_id}/photo",
        headers=headers,
        files={"file": ("late_snap.jpg", create_sample_image_bytes(), "image/jpeg")}
    )
    assert photo_res.status_code == 400
    assert "FINALIZED" in photo_res.json()["detail"]

    # Verify immutability: Cannot alter student attendance after finalization
    override_res = client.patch(
        f"/api/lectures/{lec_id}/students/{student.id}",
        json={"status": "ABSENT"},
        headers=headers
    )
    assert override_res.status_code == 400
    assert "FINALIZED" in override_res.json()["detail"]
