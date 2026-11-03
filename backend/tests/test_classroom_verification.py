import uuid
import math
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.face_recognition import get_face_recognition_service

client = TestClient(app)

def get_teacher_headers():
    uid = uuid.uuid4().hex[:6]
    reg_data = {
        "teacher_id": f"TCH-{uid}",
        "name": "Dr. Test Instructor",
        "email": f"teacher_cv_{uid}@test.edu",
        "password": "SecretPassword123",
        "department": "Computer Science"
    }
    res = client.post("/api/auth/teacher/register", json=reg_data)
    assert res.status_code == 201
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def generate_blank_image_bytes() -> bytes:
    img = np.full((400, 600, 3), 128, dtype=np.uint8)
    _, encoded = cv2.imencode(".jpg", img)
    return encoded.tobytes()

def test_model_info_and_health_check():
    res = client.get("/api/ai/model-info")
    assert res.status_code == 200
    data = res.json()
    assert data["model"] == "ArcFace-MobileFaceNet-v2"
    assert data["embedding_dimension"] == 512
    assert data["status"] == "loaded"

    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    h_data = health_res.json()
    assert h_data["database"] == "connected"
    assert h_data["face_model"] == "loaded"

def test_classroom_photo_zero_faces():
    headers = get_teacher_headers()
    lec_res = client.post("/api/lectures", json={"subject": "Zero Face Test", "division": "A"}, headers=headers)
    lec_id = lec_res.json()["id"]

    blank_bytes = generate_blank_image_bytes()
    res = client.post(
        f"/api/lectures/{lec_id}/photo",
        headers=headers,
        files=[("file", ("classroom.jpg", blank_bytes, "image/jpeg"))]
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ai_detected_count"] == 0
    assert data["unknown_faces"] == 0

def test_classroom_photo_multi_faces_and_unknown_handling(monkeypatch):
    headers = get_teacher_headers()
    rec_service = get_face_recognition_service()

    uid = uuid.uuid4().hex[:6].upper()
    student_res = client.post("/api/students", json={
        "name": "Classroom Test Student",
        "roll_no": f"CLASS-{uid}",
        "department": "AI & ML",
        "year": "2nd Year",
        "division": "A",
        "rfid_uid": f"11:22:33:{uid[:4]}"
    }, headers=headers)
    student_id = student_res.json()["id"]

    lec_res = client.post("/api/lectures", json={"subject": "Multi Face Test", "division": "A"}, headers=headers)
    lec_id = lec_res.json()["id"]

    class MockClassroomDetector:
        def detect_faces(self, img):
            return [
                (50, 50, 80, 80),    # Face 1 (Student A)
                (200, 50, 80, 80),   # Face 2 (Student A duplicate)
                (350, 50, 80, 80)    # Face 3 (Unknown)
            ]

    call_count = 0
    def mock_match_face(query_vec, enrolled_map, threshold=0.70):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {
                "status": "recognized",
                "confidence": 0.92,
                "student": {"id": student_id, "name": "Classroom Test Student", "roll_no": f"CLASS-{uid}", "department": "AI & ML"}
            }
        elif call_count == 2:
            return {
                "status": "recognized",
                "confidence": 0.95,
                "student": {"id": student_id, "name": "Classroom Test Student", "roll_no": f"CLASS-{uid}", "department": "AI & ML"}
            }
        else:
            return {
                "status": "unknown",
                "confidence": 0.41,
                "student": None
            }

    monkeypatch.setattr("app.routers.lectures.get_face_detector", lambda: MockClassroomDetector())
    monkeypatch.setattr(rec_service, "match_face", mock_match_face)

    blank_bytes = generate_blank_image_bytes()
    res = client.post(
        f"/api/lectures/{lec_id}/photo?threshold=0.70",
        headers=headers,
        files=[("file", ("classroom.jpg", blank_bytes, "image/jpeg"))]
    )

    assert res.status_code == 200
    data = res.json()

    assert data["ai_detected_count"] == 1
    assert data["unknown_faces"] == 1

def test_configurable_recognition_threshold():
    rec_service = get_face_recognition_service()
    
    v1 = [1.0] + [0.0] * 511
    v2 = [0.70, math.sqrt(1 - 0.70**2)] + [0.0] * 510

    student_map = {
        1: {
            "student": {"id": 1, "name": "Student A", "roll_no": "R01", "department": "AI"},
            "embeddings": [v2]
        }
    }

    res1 = rec_service.match_face(v1, student_map, threshold=0.65)
    assert res1["status"] == "recognized"
    assert math.isclose(res1["confidence"], 0.70, abs_tol=0.01)

    res2 = rec_service.match_face(v1, student_map, threshold=0.85)
    assert res2["status"] == "unknown"
    assert math.isclose(res2["confidence"], 0.70, abs_tol=0.01)
