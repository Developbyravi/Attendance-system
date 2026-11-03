import io
import cv2
import numpy as np
from app.models.student import StudentModel

def test_health_check_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["database"]["connected"] is True
    assert "SCRFD-10G" in data["ai_engine"]["detector"]
    assert data["ai_engine"]["detector_loaded"] is True
    assert data["ai_engine"]["embedding_dimension"] == 512

def test_classes_crud(client, admin_token):
    # List classes
    res = client.get("/api/classes")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Create division
    create_res = client.post(
        "/api/classes",
        json={"name": "C", "code": "CSE-3Y-C", "department": "Computer Science & Engineering"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_res.status_code == 200
    assert create_res.json()["name"] == "C"

def test_student_and_teacher_crud(client, admin_token):
    # Create student
    stu_res = client.post(
        "/api/students",
        json={
            "roll_no": "201",
            "name": "Alex Mercer",
            "email": "alex.mercer@smartattend.edu",
            "department": "Computer Science & Engineering",
            "division": "A",
            "rfid_uid": "CARD-ALEX-201"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert stu_res.status_code == 200
    stu_data = stu_res.json()
    stu_id = stu_data["id"]
    assert stu_data["roll_no"] == "201"

    # Create teacher
    tch_res = client.post(
        "/api/teachers",
        json={
            "teacher_id": "TCH-999",
            "name": "Dr. Banner",
            "email": "banner@smartattend.edu",
            "department": "Computer Science & Engineering",
            "assigned_divisions": ["A"]
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert tch_res.status_code == 200
    assert tch_res.json()["teacher_id"] == "TCH-999"

def test_rfid_interactive_assignment_session(client, admin_token, db_session):
    # Get or create student
    student = db_session.query(StudentModel).first()
    if not student:
        student = StudentModel(
            roll_no="999",
            name="RFID Student",
            email="rfid.student@smartattend.edu",
            division="A",
            is_active=True
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)

    # 1. Start assignment
    start_res = client.post(
        "/api/rfid/assignment/start",
        json={"student_id": student.id, "device_id": "GATE-READER-01", "timeout_seconds": 30},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert start_res.status_code == 200
    session_id = start_res.json()["session_id"]
    assert session_id is not None

    # 2. Poll session
    poll_res = client.get(f"/api/rfid/assignment/session/{session_id}")
    assert poll_res.status_code == 200
    assert poll_res.json()["status"] == "PENDING_SCAN"

    # 3. Cancel session
    cancel_res = client.post(
        "/api/rfid/assignment/cancel",
        json={"session_id": session_id}
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

def test_classroom_photo_verification_flow(client, teacher_token):
    # 1. Create a lecture session
    lec_res = client.post(
        "/api/lectures",
        json={
            "subject": "Computer Vision",
            "title": "Face Detection & Recognition",
            "division": "A",
            "lecture_date": "2026-11-03",
            "start_time": "11:00"
        },
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert lec_res.status_code == 200
    lecture_id = lec_res.json()["id"]

    # 2. Synthesize test image
    test_img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.circle(test_img, (320, 240), 80, (200, 200, 200), -1)
    success, encoded = cv2.imencode(".jpg", test_img)
    assert success

    # 3. Upload photo
    upload_res = client.post(
        f"/api/lectures/{lecture_id}/photo",
        files={"file": ("test_classroom.jpg", io.BytesIO(encoded.tobytes()), "image/jpeg")},
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert upload_res.status_code == 200
    res_data = upload_res.json()
    assert res_data["lecture_id"] == lecture_id
    assert "InsightFace SCRFD-10G" in res_data["detector"]
    assert "detected_boxes" in res_data
    assert "attendances" in res_data
