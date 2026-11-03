import uuid
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
        "email": f"teacher_xv_{uid}@test.edu",
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

def test_stage3_full_cross_verification_workflow(monkeypatch):
    """
    Tests per-lecture cross verification matrix, state machine enforcement,
    and teacher flag resolution with authentication headers.
    """
    headers = get_teacher_headers()
    rec_service = get_face_recognition_service()

    # 1. Create Lecture
    lec_res = client.post("/api/lectures", json={
        "subject": "Stage 3 Testing Lecture",
        "division": "A"
    }, headers=headers)
    assert lec_res.status_code == 201
    lecture_id = lec_res.json()["id"]

    # 2. Register 4 Enrolled Students in Division A
    uids = [uuid.uuid4().hex[:6].upper() for _ in range(4)]
    students = []
    for idx, u in enumerate(uids, start=1):
        s_res = client.post("/api/students", json={
            "name": f"Student {idx}",
            "roll_no": f"ST-{u}",
            "department": "AI & ML",
            "year": "2nd Year",
            "division": "A",
            "rfid_uid": f"11:22:33:{u[:4]}"
        }, headers=headers)
        assert s_res.status_code == 201
        students.append(s_res.json())

    st1, st2, st3, st4 = students

    # 3. Test Daily RFID Scans
    rfid_res1 = client.post("/api/attendance/rfid", json={"rfid_uid": st1["rfid_uid"]})
    assert rfid_res1.status_code == 200
    assert rfid_res1.json()["status"] == "CHECKED_IN"

    # Repeat RFID scan for Student 1 (duplicate handling)
    rfid_res1_dup = client.post("/api/attendance/rfid", json={"rfid_uid": st1["rfid_uid"]})
    assert rfid_res1_dup.status_code == 200
    assert rfid_res1_dup.json()["status"] == "ALREADY_CHECKED_IN"

    # Student 2 scans RFID
    client.post("/api/attendance/rfid", json={"rfid_uid": st2["rfid_uid"]})

    # Unknown RFID card rejection
    rfid_unk = client.post("/api/attendance/rfid", json={"rfid_uid": "99:99:99:99"})
    assert rfid_unk.status_code == 404

    # 4. Upload Classroom Photo (AI detects Student 1, Student 3, and 1 Unknown Face)
    class MockCrossDetector:
        def detect_faces(self, img):
            return [
                (10, 10, 50, 50),   # Face 1 (st1)
                (70, 70, 50, 50),   # Face 2 (st3)
                (130, 130, 50, 50)  # Face 3 (Unknown)
            ]

    call_count = 0
    def mock_match_face(query_vec, enrolled_map, threshold=0.70):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {
                "status": "recognized",
                "confidence": 0.98,
                "student": {"id": st1["id"], "name": st1["name"], "roll_no": st1["roll_no"], "department": st1["department"]}
            }
        elif call_count == 2:
            return {
                "status": "recognized",
                "confidence": 0.94,
                "student": {"id": st3["id"], "name": st3["name"], "roll_no": st3["roll_no"], "department": st3["department"]}
            }
        else:
            return {
                "status": "unknown",
                "confidence": 0.40,
                "student": None
            }

    monkeypatch.setattr("app.routers.lectures.get_face_detector", lambda: MockCrossDetector())
    monkeypatch.setattr(rec_service, "match_face", mock_match_face)

    blank_img = generate_blank_image_bytes()
    photo_res = client.post(
        f"/api/lectures/{lecture_id}/photo",
        headers=headers,
        files=[("file", ("classroom.jpg", blank_img, "image/jpeg"))]
    )
    assert photo_res.status_code == 200
    v_data = photo_res.json()

    res_map = {r["student_id"]: r for r in v_data["attendances"]}
    
    assert res_map[st1["id"]]["status"] == "PRESENT"
    assert res_map[st1["id"]]["verification_source"] == "RFID_AND_AI"
    assert res_map[st2["id"]]["status"] == "FLAGGED"
    assert res_map[st2["id"]]["verification_source"] == "RFID_ONLY"
    assert res_map[st3["id"]]["status"] == "FLAGGED"
    assert res_map[st3["id"]]["verification_source"] == "AI_ONLY"
    assert res_map[st4["id"]]["status"] in ["ABSENT", "PENDING"]

    # 5. Test Teacher Flag Resolution (Resolve st2 RFID_ONLY to CONFIRM_PRESENT)
    resolve_res = client.post(
        f"/api/lectures/{lecture_id}/resolve-flag",
        json={
            "student_id": st2["id"],
            "action": "CONFIRM_PRESENT"
        },
        headers=headers
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "PRESENT"
    assert resolve_res.json()["verification_source"] == "TEACHER_CONFIRMED"

    # 6. Finalize Session
    fin_res = client.post(f"/api/lectures/{lecture_id}/finalize", headers=headers)
    assert fin_res.status_code == 200
    assert fin_res.json()["status"] == "FINALIZED"

    # 7. Test Session Immutability after Completion
    photo_after = client.post(
        f"/api/lectures/{lecture_id}/photo",
        headers=headers,
        files=[("file", ("classroom.jpg", blank_img, "image/jpeg"))]
    )
    assert photo_after.status_code == 400
    assert "FINALIZED" in photo_after.json()["detail"]
