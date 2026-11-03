import uuid
import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.student import StudentModel
from app.models.teacher import TeacherModel
from app.models.parent import ParentModel, ParentStudentModel
from app.models.lecture_session import LectureSessionModel
from app.models.lecture_attendance import LectureAttendanceModel
from app.core.security import hash_password, create_access_token

client = TestClient(app)

def create_unique_teacher():
    uid = uuid.uuid4().hex[:6]
    db = SessionLocal()
    teacher = TeacherModel(
        teacher_id=f"TCH-{uid}",
        name=f"Prof. Test {uid}",
        email=f"teacher_{uid}@univ.edu",
        department="Computer Science & Engineering",
        password_hash=hash_password("TeacherSecret123"),
        is_active=True
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    db.close()

    token = create_access_token({"sub": str(teacher.id), "role": "TEACHER"})
    headers = {"Authorization": f"Bearer {token}"}
    return headers, teacher.id

def create_unique_student(division="A", rfid_uid=None):
    uid = uuid.uuid4().hex[:6]
    rfid = rfid_uid or f"RF:{uid[:4]}:{uid[4:]}"
    db = SessionLocal()
    student = StudentModel(
        name=f"Student {uid}",
        roll_no=f"ROLL-{uid}",
        department="Computer Science & Engineering",
        year="3rd Year",
        division=division,
        email=f"student_{uid}@univ.edu",
        rfid_uid=rfid,
        is_active=True
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    db.close()
    return student

def test_kiosk_status_and_scan():
    student = create_unique_student(rfid_uid=f"RF:GATE:{uuid.uuid4().hex[:6]}")

    # 1. Kiosk status
    status_res = client.get("/api/kiosk/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "online"

    # 2. First scan (success)
    scan_res1 = client.post("/api/kiosk/scan", json={"rfid_uid": student.rfid_uid, "device_id": "GATE-01"})
    assert scan_res1.status_code == 200
    assert scan_res1.json()["status"] == "success"
    assert scan_res1.json()["student_name"] == student.name

    # 3. Duplicate scan today
    scan_res2 = client.post("/api/kiosk/scan", json={"rfid_uid": student.rfid_uid, "device_id": "GATE-01"})
    assert scan_res2.status_code == 200
    assert scan_res2.json()["status"] == "duplicate"
    assert scan_res2.json()["scan_count"] == 2

    # 4. Unknown RFID
    scan_res3 = client.post("/api/kiosk/scan", json={"rfid_uid": "UNKNOWN_CARD_99999"})
    assert scan_res3.status_code == 404

def test_devices_classes_and_teachers_endpoints():
    headers, teacher_id = create_unique_teacher()
    student = create_unique_student(division="B")

    # 1. Devices
    while len(client.get("/api/devices").json()) < 2:
        dev_uid = uuid.uuid4().hex[:6]
        client.post("/api/devices", json={
            "device_id": f"TEST-DEV-{dev_uid}",
            "device_name": f"Test Ingress Terminal {dev_uid}",
            "location": "Main Entrance",
            "status": "online"
        })
    dev_res = client.get("/api/devices")
    assert dev_res.status_code == 200
    devices = dev_res.json()
    assert len(devices) >= 2
    assert devices[0]["status"] == "online"

    # 2. Classes
    classes_res = client.get("/api/classes")
    assert classes_res.status_code == 200
    assert len(classes_res.json()) >= 1

    # 3. Teachers
    teachers_res = client.get("/api/teachers")
    assert teachers_res.status_code == 200
    assert len(teachers_res.json()) >= 1

def test_admin_and_student_stats():
    headers, teacher_id = create_unique_teacher()
    student = create_unique_student(division="A")

    db = SessionLocal()
    lecture = LectureSessionModel(
        teacher_id=teacher_id,
        subject="Algorithms",
        division="A",
        date=date.today(),
        status="FINALIZED"
    )
    db.add(lecture)
    db.commit()
    db.refresh(lecture)

    att = LectureAttendanceModel(
        lecture_session_id=lecture.id,
        student_id=student.id,
        status="PRESENT",
        verification_source="AI_CROSSCHECK",
        rfid_checked_in=True,
        ai_detected=True,
        finalized=True
    )
    db.add(att)
    db.commit()
    db.close()

    # Admin stats
    admin_res = client.get("/api/admin/stats")
    assert admin_res.status_code == 200
    data = admin_res.json()
    assert data["total_students"] >= 1
    assert data["total_teachers"] >= 1

    # Student stats
    student_res = client.get(f"/api/student/{student.id}/stats")
    assert student_res.status_code == 200
    st_data = student_res.json()
    assert st_data["total_lectures"] >= 1
    assert st_data["present_count"] >= 1
    assert len(st_data["recent_records"]) >= 1

def test_lecture_review_roster_and_manual_override():
    headers, teacher_id = create_unique_teacher()
    student = create_unique_student(division="A")

    db = SessionLocal()
    lecture = LectureSessionModel(
        teacher_id=teacher_id,
        subject="Information Theory",
        division="A",
        date=date.today(),
        status="ACTIVE"
    )
    db.add(lecture)
    db.commit()
    db.refresh(lecture)

    att = LectureAttendanceModel(
        lecture_session_id=lecture.id,
        student_id=student.id,
        status="FLAGGED",
        verification_source="RFID_ONLY",
        rfid_checked_in=True,
        ai_detected=False,
        finalized=False
    )
    db.add(att)
    db.commit()
    lec_id = lecture.id
    stu_id = student.id
    db.close()

    # 1. Review roster
    review_res = client.get(f"/api/lectures/{lec_id}/review", headers=headers)
    assert review_res.status_code == 200
    roster = review_res.json()
    assert len(roster) >= 1
    matched = [r for r in roster if r["student_id"] == stu_id]
    assert len(matched) == 1
    assert matched[0]["attendance_status"] == "FLAGGED"

    # 2. Manual teacher override via PATCH
    patch_res = client.patch(
        f"/api/lectures/{lec_id}/students/{stu_id}",
        json={"status": "PRESENT", "reason": "Teacher visually identified student"},
        headers=headers
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["attendance_status"] == "PRESENT"

    # 3. Finalize lecture
    fin_res = client.post(f"/api/lectures/{lec_id}/finalize", headers=headers)
    assert fin_res.status_code == 200

    # 4. Immutability: attempting to override after finalization must return 400
    patch_after_fin = client.patch(
        f"/api/lectures/{lec_id}/students/{stu_id}",
        json={"status": "ABSENT"},
        headers=headers
    )
    assert patch_after_fin.status_code == 400

def test_student_deactivation():
    headers, _ = create_unique_teacher()
    rfid = f"RF:DEACT:{uuid.uuid4().hex[:6]}"
    student = create_unique_student(rfid_uid=rfid)

    deact_res = client.patch(f"/api/students/{student.id}/deactivate", headers=headers)
    assert deact_res.status_code == 200
    assert deact_res.json()["is_active"] is False

    # Scanning RFID for deactivated student must fail
    scan_res = client.post("/api/kiosk/scan", json={"rfid_uid": rfid})
    assert scan_res.status_code == 400
