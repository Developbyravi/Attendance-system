import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_teacher_auth():
    uid = uuid.uuid4().hex[:6]
    reg_data = {
        "teacher_id": f"TCH-{uid}",
        "name": "Prof. Test Instructor",
        "email": f"teacher_{uid}@univ.edu",
        "password": "TeacherPass123!",
        "department": "Computer Science"
    }
    res = client.post("/api/auth/teacher/register", json=reg_data)
    assert res.status_code == 201
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers, res.json()["user"]

def create_student_record(teacher_headers, division="A", rfid_uid=None):
    uid = uuid.uuid4().hex[:6]
    rfid = rfid_uid or f"RF:{uid[:4]}:{uid[4:]}"
    payload = {
        "name": f"Student {uid}",
        "roll_no": f"ROLL-{uid}",
        "department": "Computer Science",
        "year": "3rd Year",
        "division": division,
        "email": f"student_{uid}@univ.edu",
        "password": "StudentPass123!",
        "rfid_uid": rfid
    }
    res = client.post("/api/students", json=payload, headers=teacher_headers)
    assert res.status_code == 201
    return res.json(), payload

def test_daily_rfid_checkin_and_duplicates():
    t_headers, _ = create_teacher_auth()
    st, st_payload = create_student_record(t_headers, division="A")

    # 1. Daily RFID check-in success
    rfid_res = client.post("/api/attendance/rfid", json={"rfid_uid": st["rfid_uid"]})
    assert rfid_res.status_code == 200
    data = rfid_res.json()
    assert data["status"] == "CHECKED_IN"
    assert data["student_id"] == st["id"]

    # 2. Duplicate RFID check-in prevention
    dup_res = client.post("/api/attendance/rfid", json={"rfid_uid": st["rfid_uid"]})
    assert dup_res.status_code == 200
    assert dup_res.json()["status"] == "ALREADY_CHECKED_IN"

    # 3. Unknown RFID -> 404
    unk_res = client.post("/api/attendance/rfid", json={"rfid_uid": "99:99:99:99"})
    assert unk_res.status_code == 404

def test_create_lecture_and_division_filtering():
    t_headers, _ = create_teacher_auth()
    st_a1, _ = create_student_record(t_headers, division="A")
    st_a2, _ = create_student_record(t_headers, division="A")
    st_b1, _ = create_student_record(t_headers, division="B")

    # 4. Create lecture
    lec_res = client.post("/api/lectures", json={
        "subject": "Artificial Intelligence",
        "division": "A"
    }, headers=t_headers)
    assert lec_res.status_code == 201
    lec = lec_res.json()
    assert lec["subject"] == "Artificial Intelligence"
    assert lec["division"] == "A"

    # 5. Get lecture details - verify Division B student is not included in Division A lecture
    get_lec = client.get(f"/api/lectures/{lec['id']}", headers=t_headers)
    assert get_lec.status_code == 200

def test_lecture_verification_cases_and_finalization():
    t_headers, _ = create_teacher_auth()

    # Create Division A students:
    # st1: RFID scanned, AI detected -> PRESENT
    # st2: RFID scanned, AI NOT detected -> FLAGGED (RFID_ONLY)
    # st3: RFID NOT scanned, AI detected -> FLAGGED (AI_ONLY)
    # st4: Neither -> ABSENT
    st1, _ = create_student_record(t_headers, division="A")
    st2, _ = create_student_record(t_headers, division="A")
    st3, _ = create_student_record(t_headers, division="A")
    st4, _ = create_student_record(t_headers, division="A")

    # Perform morning RFID check-in for st1 and st2
    client.post("/api/attendance/rfid", json={"rfid_uid": st1["rfid_uid"]})
    client.post("/api/attendance/rfid", json={"rfid_uid": st2["rfid_uid"]})

    # Create lecture
    lec_res = client.post("/api/lectures", json={"subject": "Machine Learning", "division": "A"}, headers=t_headers)
    lec_id = lec_res.json()["id"]

    # 11. Flag Resolution
    # Manually update attendance or resolve flag
    # First finalize lecture test
    fin_res = client.post(f"/api/lectures/{lec_id}/finalize", headers=t_headers)
    assert fin_res.status_code == 200
    assert fin_res.json()["status"] == "FINALIZED"

    # 13. Finalized record immutability
    dup_fin = client.post(f"/api/lectures/{lec_id}/finalize", headers=t_headers)
    assert dup_fin.status_code == 400

    resolve_err = client.post(f"/api/lectures/{lec_id}/resolve-flag", json={"student_id": st1["id"], "action": "CONFIRM_PRESENT"}, headers=t_headers)
    assert resolve_err.status_code == 400

def test_student_security_and_portal_access():
    t_headers, _ = create_teacher_auth()
    st1, payload1 = create_student_record(t_headers, division="A")
    st2, payload2 = create_student_record(t_headers, division="A")

    # Login student 1
    s1_login = client.post("/api/auth/student/login", json={"email_or_roll": payload1["email"], "password": payload1["password"]})
    assert s1_login.status_code == 200
    s1_token = s1_login.json()["access_token"]
    s1_headers = {"Authorization": f"Bearer {s1_token}"}

    # 14. Student sees own attendance
    st1_att = client.get("/api/student/me/attendance", headers=s1_headers)
    assert st1_att.status_code == 200
    assert st1_att.json()["student_id"] == st1["id"]

    # 16. Student cannot access teacher API
    forbidden = client.get("/api/lectures", headers=s1_headers)
    assert forbidden.status_code == 403

    # 17. Teacher authorization checks
    unauth = client.get("/api/lectures")
    assert unauth.status_code == 401
