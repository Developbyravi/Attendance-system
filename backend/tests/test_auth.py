import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_teacher_auth_headers():
    uid = uuid.uuid4().hex[:6]
    reg_data = {
        "teacher_id": f"TCH-{uid}",
        "name": "Dr. Test Instructor",
        "email": f"teacher_{uid}@test.edu",
        "password": "SecretPassword123",
        "department": "Computer Science"
    }
    res = client.post("/api/auth/teacher/register", json=reg_data)
    assert res.status_code == 201
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, reg_data

def test_teacher_registration_and_login():
    uid = uuid.uuid4().hex[:6]
    reg_payload = {
        "teacher_id": f"TCH-{uid}",
        "name": "Prof. Alan Turing",
        "email": f"turing_{uid}@university.edu",
        "password": "SecurePassword!2026",
        "department": "AI & ML"
    }
    # Register teacher
    reg_res = client.post("/api/auth/teacher/register", json=reg_payload)
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert "access_token" in data
    assert data["role"] == "TEACHER"
    assert data["user"]["email"] == reg_payload["email"]

    # Duplicate email registration rejection
    dup_res = client.post("/api/auth/teacher/register", json=reg_payload)
    assert dup_res.status_code == 400

    # Successful login
    login_res = client.post("/api/auth/teacher/login", json={
        "email": reg_payload["email"],
        "password": reg_payload["password"]
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Wrong password login failure
    wrong_pwd_res = client.post("/api/auth/teacher/login", json={
        "email": reg_payload["email"],
        "password": "WrongPassword123"
    })
    assert wrong_pwd_res.status_code == 401

def test_unauthenticated_and_role_protection():
    # 1. Unauthenticated request -> 401
    unauth_res = client.get("/api/students")
    assert unauth_res.status_code == 401

    # 2. Teacher setup & student creation
    headers, _ = get_teacher_auth_headers()
    uid = uuid.uuid4().hex[:6]
    student_payload = {
        "name": "Portal Student",
        "roll_no": f"STU-{uid}",
        "department": "Computer Science",
        "year": "2nd Year",
        "email": f"student_{uid}@test.edu",
        "password": "StudentPassword123",
        "rfid_uid": f"11:22:{uid[:4]}"
    }
    create_st_res = client.post("/api/students", json=student_payload, headers=headers)
    assert create_st_res.status_code == 201

    # 3. Student login
    st_login_res = client.post("/api/auth/student/login", json={
        "email_or_roll": student_payload["email"],
        "password": student_payload["password"]
    })
    assert st_login_res.status_code == 200
    st_token = st_login_res.json()["access_token"]
    st_headers = {"Authorization": f"Bearer {st_token}"}

    # 4. Student accessing teacher endpoint -> 403 Forbidden
    forbidden_res = client.get("/api/students", headers=st_headers)
    assert forbidden_res.status_code == 403

    # 5. Student accessing their own portal endpoints -> 200 OK
    profile_res = client.get("/api/student/me/profile", headers=st_headers)
    assert profile_res.status_code == 200
    assert profile_res.json()["roll_no"] == student_payload["roll_no"]

    attendance_res = client.get("/api/student/me/attendance", headers=st_headers)
    assert attendance_res.status_code == 200
    assert "today_lectures" in attendance_res.json()

def test_student_and_unified_registration():
    uid = uuid.uuid4().hex[:6]
    # 1. Register student via unified /register endpoint
    st_payload = {
        "role": "STUDENT",
        "name": f"New Student {uid}",
        "roll_no": f"REG-{uid}",
        "email": f"st_reg_{uid}@test.edu",
        "password": "Password123!",
        "department": "Computer Science",
        "year": "3rd Year",
        "division": "A"
    }
    st_res = client.post("/api/auth/register", json=st_payload)
    assert st_res.status_code == 201
    st_data = st_res.json()
    assert "access_token" in st_data
    assert st_data["role"] == "STUDENT"
    assert st_data["user"]["roll_no"] == f"REG-{uid}"

    # 2. Register parent via unified /register endpoint
    p_uid = uuid.uuid4().hex[:6]
    parent_payload = {
        "role": "PARENT",
        "name": f"Parent {p_uid}",
        "phone": f"+1555{p_uid}",
        "email": f"parent_{p_uid}@test.edu",
        "password": "ParentPassword123!"
    }
    parent_res = client.post("/api/auth/register", json=parent_payload)
    assert parent_res.status_code == 201
    p_data = parent_res.json()
    assert "access_token" in p_data
    assert p_data["role"] == "PARENT"
    assert p_data["user"]["name"] == f"Parent {p_uid}"
