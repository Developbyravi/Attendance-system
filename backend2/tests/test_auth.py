def test_login_and_token_generation(client, admin_token):
    # Test valid login with seeded admin credentials
    response = client.post(
        "/api/auth/token",
        data={"username": "test_admin@smartattend.edu", "password": "Admin@123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(client):
    response = client.post(
        "/api/auth/token",
        data={"username": "test_admin@smartattend.edu", "password": "WrongPassword!"}
    )
    assert response.status_code == 401

def test_auth_me_endpoint(client, teacher_token):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test_teacher@smartattend.edu"
    assert data["role"] == "teacher"

def test_role_enforcement_admin_only(client, student_token, admin_token):
    # Student trying to list teachers (requires admin)
    res_student = client.get(
        "/api/teachers",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_student.status_code == 403

    # Admin listing teachers
    res_admin = client.get(
        "/api/teachers",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_admin.status_code == 200

def test_unauthorized_teacher_registration_rejected(client, student_token):
    # Public unauthenticated registration with role="TEACHER" must be rejected (403)
    res_unauth = client.post(
        "/api/auth/register",
        json={
            "email": "hacker_teacher@smartattend.edu",
            "password": "Password123!",
            "name": "Malicious Teacher",
            "role": "TEACHER"
        }
    )
    assert res_unauth.status_code == 403

    # Authenticated student trying to register a teacher must also be rejected (403)
    res_student = client.post(
        "/api/auth/register",
        json={
            "email": "student_attempt_teacher@smartattend.edu",
            "password": "Password123!",
            "name": "Student Attempter",
            "role": "TEACHER"
        },
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_student.status_code == 403

def test_public_student_registration_allowed(client):
    # Public registration with role="STUDENT" must succeed (200)
    res = client.post(
        "/api/auth/register",
        json={
            "email": "fresh_student@smartattend.edu",
            "password": "Password123!",
            "name": "Fresh Student",
            "roll_no": "STU-9999",
            "role": "STUDENT",
            "department": "Computer Science & Engineering",
            "division": "A"
        }
    )
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_invalid_and_expired_tokens(client):
    # Invalid signature or malformed token
    res_invalid = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer not.a.valid.jwt.token"}
    )
    assert res_invalid.status_code == 401

    # Missing authorization header
    res_missing = client.get("/api/auth/me")
    assert res_missing.status_code == 401

