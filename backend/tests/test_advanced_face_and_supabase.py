import os
import uuid
import json
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
from app.services.supabase_service import get_supabase_service
from app.core.security import create_access_token

client = TestClient(app)

def get_auth_token(user_id: int, role: str):
    return create_access_token({"sub": str(user_id), "role": role})

def test_face_recognition_ambiguity_detection():
    """Verifies that if two enrolled students have near-tie similarity scores, status is ambiguous."""
    rec_service = get_face_recognition_service()
    enrolled_map = {
        101: {
            "student": {"id": 101, "name": "Student A", "roll_no": "A-01"},
            "embeddings": [[0.5] * 512]
        },
        102: {
            "student": {"id": 102, "name": "Student B", "roll_no": "B-02"},
            "embeddings": [[0.51] * 512] # Very close embedding vector
        }
    }
    query_vec = [0.505] * 512
    # Match face with ambiguity threshold check
    res = rec_service.match_face(query_vec, enrolled_map, threshold=0.70)
    # Cosine similarity between proportional vectors is ~1.0, and diff < 0.08 -> ambiguous
    assert res["status"] == "ambiguous"
    assert "ambiguity_details" in res
    assert res["ambiguity_details"]["primary_candidate"]["id"] in [101, 102]

def test_face_recognition_deduplication():
    """Verifies that multiple detections of the same student keep the highest score and record duplicates."""
    rec_service = get_face_recognition_service()
    enrolled_map = {
        201: {
            "student": {"id": 201, "name": "Unique Student", "roll_no": "U-01"},
            "embeddings": [[0.9] * 512]
        }
    }
    # Simulate 2 detections matching student 201 with different crops
    detected_faces = [
        {"face_crop": None, "conf": 0.85, "bbox": (10, 10, 40, 40)},
        {"face_crop": None, "conf": 0.90, "bbox": (60, 60, 40, 40)}
    ]

    # Mock generate_embedding to return close vector
    orig_gen = rec_service.generate_embedding
    try:
        rec_service.generate_embedding = lambda crop: [0.9] * 512
        results = rec_service.process_classroom_detections(detected_faces, enrolled_map, threshold=0.70)
        assert 201 in results["recognized"]
        assert len(results["duplicates"]) == 1 # 1 duplicate recorded
    finally:
        rec_service.generate_embedding = orig_gen

def test_inactive_student_rfid_rejection():
    """Verifies that an inactive student account is rejected for RFID checkin."""
    db = SessionLocal()
    try:
        uid = uuid.uuid4().hex[:6]
        student = StudentModel(
            name="Inactive Test",
            roll_no=f"INACT-{uid}",
            department="CS",
            year="1st",
            division="A",
            rfid_uid=f"INACT:{uid}",
            is_active=False
        )
        db.add(student)
        db.commit()

        res = client.post("/api/attendance/rfid", json={"rfid_uid": f"INACT:{uid}"})
        assert res.status_code == 400
        assert "inactive" in res.json()["detail"].lower()
    finally:
        db.close()

def test_post_finalization_immutability():
    """Verifies that once a lecture is finalized, no further photo uploads or flag resolutions are permitted."""
    db = SessionLocal()
    try:
        # Create teacher and lecture
        uid = uuid.uuid4().hex[:6]
        teacher = TeacherModel(
            teacher_id=f"TCH-{uid}",
            name="Finalize Teacher",
            email=f"finalize_{uid}@test.edu",
            password_hash="mock",
            department="CS"
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)

        token = get_auth_token(teacher.id, "TEACHER")
        headers = {"Authorization": f"Bearer {token}"}

        lec_res = client.post("/api/lectures", json={"subject": "Imm Test", "division": "A"}, headers=headers)
        assert lec_res.status_code == 201
        lec_id = lec_res.json()["id"]

        # Finalize lecture
        fin_res = client.post(f"/api/lectures/{lec_id}/finalize", headers=headers)
        assert fin_res.status_code == 200
        assert fin_res.json()["status"] == "FINALIZED"

        # Try to finalize again -> 400
        fin_again = client.post(f"/api/lectures/{lec_id}/finalize", headers=headers)
        assert fin_again.status_code == 400

        # Try to resolve flag -> 400
        flag_res = client.post(
            f"/api/lectures/{lec_id}/resolve-flag",
            json={"student_id": 9999, "action": "CONFIRM_PRESENT"},
            headers=headers
        )
        assert flag_res.status_code == 400
        assert "finalized" in flag_res.json()["detail"].lower()
    finally:
        db.close()

def test_cross_role_access_boundary():
    """Verifies role-level boundary enforcement (Student cannot create lectures or call teacher endpoints)."""
    db = SessionLocal()
    try:
        uid = uuid.uuid4().hex[:6]
        student = StudentModel(
            name="Bound Student",
            roll_no=f"BND-{uid}",
            department="CS",
            year="1st",
            division="A",
            rfid_uid=f"BND:{uid}",
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        token = get_auth_token(student.id, "STUDENT")
        headers = {"Authorization": f"Bearer {token}"}

        # Student attempting to create lecture -> 403 Forbidden
        lec_res = client.post("/api/lectures", json={"subject": "Hacked Lecture", "division": "A"}, headers=headers)
        assert lec_res.status_code == 403

        # Student attempting to list all students -> 403 Forbidden
        stud_res = client.get("/api/students", headers=headers)
        assert stud_res.status_code == 403

        # Student accessing own profile -> 200 OK
        me_res = client.get("/api/student/me/profile", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["roll_no"] == f"BND-{uid}"
    finally:
        db.close()

def test_supabase_service_fallback_and_audit():
    """Verifies that SupabaseService operates gracefully in local/fallback mode without external credentials."""
    svc = get_supabase_service()
    assert svc is not None

    # Test classroom image upload fallback
    res = svc.upload_classroom_image(lecture_id=999, file_bytes=b"mock-image-data", filename="test.jpg")
    assert "url" in res
    assert "storage" in res

    # Test audit log event recording
    db = SessionLocal()
    try:
        svc.log_audit_event(
            user_id="test_admin",
            role="ADMIN",
            action="TEST_ACTION",
            entity_type="SYSTEM",
            entity_id="1",
            details={"test": True},
            db_session=db
        )
    finally:
        db.close()
