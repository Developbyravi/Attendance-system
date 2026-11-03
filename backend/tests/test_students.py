import io
import uuid
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_teacher_headers():
    uid = uuid.uuid4().hex[:6]
    reg_data = {
        "teacher_id": f"TCH-{uid}",
        "name": "Dr. Test Instructor",
        "email": f"teacher_st_{uid}@test.edu",
        "password": "SecretPassword123",
        "department": "Computer Science"
    }
    res = client.post("/api/auth/teacher/register", json=reg_data)
    assert res.status_code == 201
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def generate_blank_image_bytes() -> bytes:
    img = np.full((300, 300, 3), 128, dtype=np.uint8)
    _, encoded = cv2.imencode(".jpg", img)
    return encoded.tobytes()

def test_create_and_get_student():
    headers = get_teacher_headers()
    uid = uuid.uuid4().hex[:6].upper()
    payload = {
        "name": "Test Student",
        "roll_no": f"TEST-{uid}",
        "department": "AI & ML",
        "year": "2nd Year",
        "rfid_uid": f"AA:BB:CC:{uid[:4]}"
    }
    create_res = client.post("/api/students", json=payload, headers=headers)
    assert create_res.status_code == 201, f"Failed: {create_res.text}"
    created_data = create_res.json()
    assert created_data["name"] == payload["name"]
    assert created_data["face_enrolled"] is False
    student_id = created_data["id"]

    get_res = client.get(f"/api/students/{student_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == student_id

    list_res = client.get("/api/students", headers=headers)
    assert list_res.status_code == 200
    assert any(s["id"] == student_id for s in list_res.json())

def test_reject_zero_faces_image():
    headers = get_teacher_headers()
    uid = uuid.uuid4().hex[:6].upper()
    payload = {
        "name": "No Face Student",
        "roll_no": f"NOFACE-{uid}",
        "department": "AI & ML",
        "year": "1st Year",
        "rfid_uid": f"00:11:22:{uid[:4]}"
    }
    create_res = client.post("/api/students", json=payload, headers=headers)
    assert create_res.status_code == 201
    student_id = create_res.json()["id"]

    blank_bytes = generate_blank_image_bytes()
    enroll_res = client.post(
        f"/api/students/{student_id}/face-enroll",
        headers=headers,
        files=[("files", ("blank.jpg", blank_bytes, "image/jpeg"))]
    )

    assert enroll_res.status_code == 400
    assert "No face detected" in enroll_res.json()["detail"]

def test_mocked_single_and_multi_face_enrollment(monkeypatch):
    headers = get_teacher_headers()
    uid = uuid.uuid4().hex[:6].upper()
    payload = {
        "name": "Enrollment Student",
        "roll_no": f"ENROLL-{uid}",
        "department": "AI & ML",
        "year": "2nd Year",
        "rfid_uid": f"EE:FF:11:{uid[:4]}"
    }
    create_res = client.post("/api/students", json=payload, headers=headers)
    assert create_res.status_code == 201, f"Failed: {create_res.text}"
    student_id = create_res.json()["id"]

    dummy_img_bytes = generate_blank_image_bytes()

    # 1. Test Multi-face rejection (Mock 2 faces detected)
    class MockMultiFaceDetector:
        def detect_faces(self, img):
            return [(10, 10, 50, 50), (100, 100, 50, 50)]

    monkeypatch.setattr("app.services.image_processor.get_face_detector", lambda: MockMultiFaceDetector())

    multi_res = client.post(
        f"/api/students/{student_id}/face-enroll",
        headers=headers,
        files=[("files", ("multi.jpg", dummy_img_bytes, "image/jpeg"))]
    )
    assert multi_res.status_code == 400
    assert "Multiple faces detected" in multi_res.json()["detail"]

    # 2. Test Successful Single-face enrollment (Mock 1 face detected)
    class MockSingleFaceDetector:
        def detect_faces(self, img):
            return [(20, 20, 100, 100)]

    monkeypatch.setattr("app.services.image_processor.get_face_detector", lambda: MockSingleFaceDetector())

    single_res = client.post(
        f"/api/students/{student_id}/face-enroll",
        headers=headers,
        files=[("files", ("face1.jpg", dummy_img_bytes, "image/jpeg"))]
    )
    assert single_res.status_code == 200
    res_data = single_res.json()
    assert res_data["student_id"] == student_id
    assert res_data["successful_embeddings"] == 1
    assert res_data["status"] == "enrolled"

    # Verify student record reflects face_enrolled = True
    student_res = client.get(f"/api/students/{student_id}", headers=headers)
    assert student_res.json()["face_enrolled"] is True
