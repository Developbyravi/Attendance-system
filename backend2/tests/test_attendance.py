def test_lecture_lifecycle_and_immutability(client, teacher_token):
    # 1. Create lecture session
    lec_payload = {
        "subject": "Deep Learning",
        "title": "Convolutional Neural Networks",
        "division": "A",
        "division_id": "A",
        "lecture_date": "2026-11-03",
        "start_time": "10:00",
        "classroom": "Room 402"
    }

    create_res = client.post(
        "/api/lectures",
        json=lec_payload,
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert create_res.status_code == 200
    lec = create_res.json()
    lecture_id = lec["id"]
    assert lec["subject"] == "Deep Learning"
    assert lec["status"] == "scheduled"

    # 2. Get lecture details
    get_res = client.get(
        f"/api/lectures/{lecture_id}",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Convolutional Neural Networks"

    # 3. Finalize lecture session
    fin_res = client.post(
        f"/api/lectures/{lecture_id}/finalize",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert fin_res.status_code == 200
    fin_data = fin_res.json()
    assert fin_data["finalized"] is True

    # 4. Attempt to modify student attendance on finalized lecture -> MUST BE REJECTED (400)
    override_res = client.patch(
        f"/api/lectures/{lecture_id}/students/101",
        json={"status": "PRESENT", "reason": "Teacher attempt after finalization"},
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert override_res.status_code == 400

def test_teacher_lecture_isolation(client, teacher_token, admin_token, db_session):
    from app.models.user import UserModel
    from app.models.teacher import TeacherModel
    from app.core.security import get_password_hash, create_access_token

    # Create Teacher 2
    u2 = UserModel(
        email="teacher2@smartattend.edu",
        username="teacher2",
        full_name="Prof. Second Teacher",
        hashed_password=get_password_hash("Password123!"),
        role="TEACHER",
        is_active=True
    )
    db_session.add(u2)
    db_session.commit()
    t2 = TeacherModel(
        user_id=u2.id,
        teacher_id="EMP-9002",
        name="Prof. Second Teacher",
        email="teacher2@smartattend.edu",
        department="Computer Science & Engineering",
        is_active=True
    )
    db_session.add(t2)
    db_session.commit()

    teacher2_token = create_access_token({"sub": u2.email, "user_id": u2.id, "role": "TEACHER", "email": u2.email})

    # Teacher 1 creates a lecture
    lec_payload = {
        "subject": "Compiler Design",
        "title": "Lexical Analysis",
        "division": "A",
        "division_id": "A",
        "lecture_date": "2026-11-03",
        "start_time": "14:00"
    }
    create_res = client.post(
        "/api/lectures",
        json=lec_payload,
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert create_res.status_code == 200
    lecture_id = create_res.json()["id"]

    # Teacher 2 attempts to review Teacher 1's lecture -> MUST BE REJECTED (403)
    review_res = client.get(
        f"/api/lectures/{lecture_id}/review",
        headers={"Authorization": f"Bearer {teacher2_token}"}
    )
    assert review_res.status_code == 403

    # Teacher 2 attempts to finalize Teacher 1's lecture -> MUST BE REJECTED (403)
    fin_res = client.post(
        f"/api/lectures/{lecture_id}/finalize",
        headers={"Authorization": f"Bearer {teacher2_token}"}
    )
    assert fin_res.status_code == 403

def test_attendance_audit_log_persisted(client, teacher_token, db_session):
    from app.models.attendance import AttendanceAuditLogModel

    # Create and finalize a lecture
    lec_payload = {
        "subject": "Database Systems",
        "title": "Transaction Isolation",
        "division": "A",
        "division_id": "A",
        "lecture_date": "2026-11-03",
        "start_time": "11:00"
    }
    create_res = client.post(
        "/api/lectures",
        json=lec_payload,
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert create_res.status_code == 200
    lecture_id = create_res.json()["id"]

    # Finalize
    client.post(
        f"/api/lectures/{lecture_id}/finalize",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )

    # Check audit log in DB
    logs = db_session.query(AttendanceAuditLogModel).filter(
        AttendanceAuditLogModel.action == "FINALIZE_LECTURE",
        AttendanceAuditLogModel.entity_id == str(lecture_id)
    ).all()
    assert len(logs) >= 1
    log = logs[0]
    assert log.role == "TEACHER"
    assert "total_records" in log.details_dict

