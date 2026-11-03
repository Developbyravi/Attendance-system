import uuid
import time
import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.config import settings
from app.models.student import StudentModel
from app.models.teacher import TeacherModel
from app.models.daily_checkin import DailyCheckinModel
from app.core.security import hash_password, create_access_token

client = TestClient(app)

def create_admin_headers():
    admin_uuid = str(uuid.uuid4())
    token = create_access_token({"sub": admin_uuid, "role": "ADMIN", "email": "admin@smartattend.edu"})
    return {"Authorization": f"Bearer {token}"}

def create_teacher_headers():
    db = SessionLocal()
    uid = uuid.uuid4().hex[:6]
    teacher = TeacherModel(
        teacher_id=f"TCH-{uid}",
        name=f"Prof. {uid}",
        email=f"prof_{uid}@univ.edu",
        department="AI & ML",
        password_hash=hash_password("TeacherSecret123"),
        is_active=True
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    db.close()
    token = create_access_token({"sub": str(teacher.id), "role": "TEACHER"})
    return {"Authorization": f"Bearer {token}"}

def create_student_with_auth(rfid_uid=None, is_active=True):
    db = SessionLocal()
    uid = uuid.uuid4().hex[:6]
    rfid = rfid_uid or f"RF:{uid[:4]}:{uid[4:]}".upper()
    student = StudentModel(
        name=f"Student {uid}",
        roll_no=f"ROLL-{uid}",
        department="Computer Science & Engineering",
        year="2nd Year",
        division="A",
        email=f"student_{uid}@univ.edu",
        rfid_uid=rfid,
        is_active=is_active
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    student_id = student.id
    db.close()

    token = create_access_token({"sub": str(student_id), "role": "STUDENT"})
    return student, {"Authorization": f"Bearer {token}"}

# ── 1. ROLE-BASED ACCESS CONTROL (RBAC) ENFORCEMENT ──
def test_admin_only_access_control():
    admin_headers = create_admin_headers()
    teacher_headers = create_teacher_headers()
    student, student_headers = create_student_with_auth()

    start_payload = {
        "student_id": student.id,
        "mode": "ASSIGN",
        "device_id": "GATE-READER-01",
        "timeout_seconds": 60
    }

    # 1. Admin can initiate assignment
    admin_res = client.post("/api/rfid/assignment/start", json=start_payload, headers=admin_headers)
    assert admin_res.status_code == 200, f"Admin should be authorized: {admin_res.text}"
    session_id = admin_res.json()["session_id"]

    # 2. Student cannot initiate assignment (403 Forbidden)
    student_res = client.post("/api/rfid/assignment/start", json=start_payload, headers=student_headers)
    assert student_res.status_code == 403, "Students must not initiate card assignment"

    # 3. Teacher cannot initiate assignment without admin role (403 Forbidden)
    teacher_res = client.post("/api/rfid/assignment/start", json=start_payload, headers=teacher_headers)
    assert teacher_res.status_code == 403, "Teachers must not initiate card assignment"

    # 4. Student cannot confirm assignment (403 Forbidden)
    confirm_payload = {
        "session_id": session_id,
        "student_id": student.id,
        "rfid_uid": "E2:34:56:78"
    }
    st_confirm_res = client.post("/api/rfid/assignment/confirm", json=confirm_payload, headers=student_headers)
    assert st_confirm_res.status_code == 403, "Students must not confirm RFID assignment"

    # 5. Teacher cannot alter RFID UID via direct PUT /api/students/{id}
    tch_update_res = client.put(
        f"/api/students/{student.id}",
        json={"rfid_uid": "99:88:77:66"},
        headers=teacher_headers
    )
    assert tch_update_res.status_code == 403, "Teachers must not arbitrarily alter student RFID cards"

# ── 2. SEPARATION OF CARD ASSIGNMENT FROM DAILY ATTENDANCE ──
def test_hardware_scan_separation_from_attendance():
    admin_headers = create_admin_headers()
    student, _ = create_student_with_auth(rfid_uid=f"UNASSIGNED-{uuid.uuid4().hex[:6].upper()}")

    # Start assignment session on reader
    device_id = f"GATE-READER-{uuid.uuid4().hex[:4].upper()}"
    start_res = client.post("/api/rfid/assignment/start", json={
        "student_id": student.id,
        "device_id": device_id,
        "timeout_seconds": 60
    }, headers=admin_headers)
    assert start_res.status_code == 200
    session_id = start_res.json()["session_id"]

    # Physical card tapped on reader
    new_scanned_uid = f"E4:A1:B2:{uuid.uuid4().hex[:4].upper()}"
    scan_res = client.post(
        "/api/kiosk/scan",
        json={"rfid_uid": new_scanned_uid, "device_id": device_id},
        headers={"X-Device-API-Key": settings.DEVICE_API_KEY}
    )
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["status"] == "assignment_captured"
    assert scan_data["mode"] == "assignment"
    assert scan_data["rfid_uid"] == new_scanned_uid
    assert scan_data["session_id"] == session_id

    # CRITICAL CHECK: Verify attendance was NOT marked for this student
    db = SessionLocal()
    today_checkin = db.query(DailyCheckinModel).filter(
        DailyCheckinModel.student_id == student.id,
        DailyCheckinModel.date == date.today()
    ).first()
    db.close()
    assert today_checkin is None, "Card scan during assignment mode must NOT mark attendance!"

    # Polling the session reveals SCANNED state with real scanned UID
    poll_res = client.get(f"/api/rfid/assignment/session/{session_id}", headers=admin_headers)
    assert poll_res.status_code == 200
    poll_data = poll_res.json()
    assert poll_data["status"] == "SCANNED"
    assert poll_data["scanned_uid"] == new_scanned_uid

# ── 3. ADMIN CONFIRMATION, DATABASE BINDING & AUDIT LOGGING ──
def test_admin_confirm_card_assignment():
    admin_headers = create_admin_headers()
    student, _ = create_student_with_auth()

    device_id = f"GATE-{uuid.uuid4().hex[:4].upper()}"
    start_res = client.post("/api/rfid/assignment/start", json={
        "student_id": student.id,
        "device_id": device_id,
        "timeout_seconds": 60
    }, headers=admin_headers)
    session_id = start_res.json()["session_id"]

    new_uid = f"F1:02:C3:{uuid.uuid4().hex[:4].upper()}"
    client.post(
        "/api/rfid/scan",
        json={"rfid_uid": new_uid, "device_id": device_id},
        headers={"X-Device-API-Key": settings.DEVICE_API_KEY}
    )

    # Admin confirms assignment
    confirm_res = client.post("/api/rfid/assignment/confirm", json={
        "session_id": session_id,
        "student_id": student.id,
        "rfid_uid": new_uid,
        "reason": "Official freshman card issuance"
    }, headers=admin_headers)
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    assert confirm_data["status"] == "success"
    assert confirm_data["rfid_uid"] == new_uid

    # Verify student in database now has the new card UID
    db = SessionLocal()
    updated_student = db.query(StudentModel).filter(StudentModel.id == student.id).first()
    assert updated_student.rfid_uid == new_uid
    db.close()

# ── 4. UID UNIQUENESS CONFLICT REJECTION (409 CONFLICT) ──
def test_uid_uniqueness_conflict_rejection():
    admin_headers = create_admin_headers()
    card_uid = f"SHARED:CARD:{uuid.uuid4().hex[:4].upper()}"

    # Student 1 already possesses this card
    student1, _ = create_student_with_auth(rfid_uid=card_uid)
    # Student 2 is a different active student
    student2, _ = create_student_with_auth(rfid_uid=f"DIFF:{uuid.uuid4().hex[:4].upper()}")

    device_id = f"READER-{uuid.uuid4().hex[:4].upper()}"
    start_res = client.post("/api/rfid/assignment/start", json={
        "student_id": student2.id,
        "device_id": device_id,
        "timeout_seconds": 60
    }, headers=admin_headers)
    session_id = start_res.json()["session_id"]

    # Ingest the card UID that already belongs to student 1
    client.post(
        "/api/kiosk/scan",
        json={"rfid_uid": card_uid, "device_id": device_id},
        headers={"X-Device-API-Key": settings.DEVICE_API_KEY}
    )

    # Admin attempts to confirm card for student 2 -> Must be rejected with 409 Conflict
    confirm_res = client.post("/api/rfid/assignment/confirm", json={
        "session_id": session_id,
        "student_id": student2.id,
        "rfid_uid": card_uid,
        "reason": "Accidental duplicate card scan"
    }, headers=admin_headers)

    assert confirm_res.status_code == 409, f"Expected 409 Conflict for duplicate card UID, got {confirm_res.status_code}"
    assert "already assigned to active student" in confirm_res.json()["detail"]

# ── 5. CARD DEACTIVATION WORKFLOW ──
def test_card_deactivation_workflow():
    admin_headers = create_admin_headers()
    student, _ = create_student_with_auth()
    active_uid = student.rfid_uid

    # Deactivate active student card
    deact_res = client.post("/api/rfid/deactivate", json={
        "student_id": student.id,
        "reason": "Card reported lost by student"
    }, headers=admin_headers)
    assert deact_res.status_code == 200
    assert deact_res.json()["deactivated_rfid_uid"] == active_uid

    # Database verification
    db = SessionLocal()
    st = db.query(StudentModel).filter(StudentModel.id == student.id).first()
    assert st.rfid_uid.startswith("DEACTIVATED-")
    db.close()

    # Attempting to deactivate again returns 400 Bad Request
    deact_again = client.post("/api/rfid/deactivate", json={
        "student_id": student.id,
        "reason": "Repeat deactivation"
    }, headers=admin_headers)
    assert deact_again.status_code == 400
    assert "does not have an active assigned RFID card" in deact_again.json()["detail"]

# ── 6. SESSION TIMEOUT AND CANCELLATION ──
def test_session_cancellation_and_timeout():
    admin_headers = create_admin_headers()
    student, _ = create_student_with_auth()

    # Cancellation test
    start_res = client.post("/api/rfid/assignment/start", json={
        "student_id": student.id,
        "device_id": "GATE-01",
        "timeout_seconds": 60
    }, headers=admin_headers)
    session_id = start_res.json()["session_id"]

    cancel_res = client.post("/api/rfid/assignment/cancel", json={"session_id": session_id}, headers=admin_headers)
    assert cancel_res.status_code == 200

    poll_res = client.get(f"/api/rfid/assignment/session/{session_id}", headers=admin_headers)
    assert poll_res.json()["status"] == "CANCELLED"

    # Timeout test: session initialized with minimum timeout
    start_exp = client.post("/api/rfid/assignment/start", json={
        "student_id": student.id,
        "device_id": "GATE-02",
        "timeout_seconds": 10
    }, headers=admin_headers)
    exp_session_id = start_exp.json()["session_id"]

    # Artificially expire the session in manager to test expiration handling
    from app.services.rfid_assignment_manager import get_rfid_assignment_manager
    manager = get_rfid_assignment_manager()
    session_obj = manager.get_session(exp_session_id)
    session_obj.expires_at = time.time() - 1 # Set to past

    poll_exp = client.get(f"/api/rfid/assignment/session/{exp_session_id}", headers=admin_headers)
    assert poll_exp.json()["status"] == "EXPIRED"

# ── 7. SECURE DEVICE AUTHENTICATION ──
def test_device_api_key_security():
    # Ingest without X-Device-API-Key should be rejected with 401
    unauth_res = client.post(
        "/api/rfid/scan",
        json={"rfid_uid": "01:02:03:04", "device_id": "GATE-01"}
    )
    assert unauth_res.status_code == 401, "Device endpoint must reject unauthenticated requests"

    # Ingest with wrong key should be rejected with 401
    bad_res = client.post(
        "/api/rfid/scan",
        json={"rfid_uid": "01:02:03:04", "device_id": "GATE-01"},
        headers={"X-Device-API-Key": "INVALID-DEVICE-KEY"}
    )
    assert bad_res.status_code == 401, "Device endpoint must reject invalid API keys"
