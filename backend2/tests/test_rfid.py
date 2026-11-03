def test_daily_rfid_checkin_flow(client, teacher_token, student_token):
    # Student has RFID "TEST-UID-101"
    # 1. First morning scan -> SUCCESS
    res1 = client.post(
        "/api/attendance/rfid",
        json={"rfid_uid": "TEST-UID-101", "device_id": "GATE-READER-01"}
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "SUCCESS"
    assert data1["student"]["name"] == "Student Test"

    # 2. Second scan same day -> ALREADY_CHECKED_IN (idempotent, does not error)
    res2 = client.post(
        "/api/attendance/rfid",
        json={"rfid_uid": "TEST-UID-101", "device_id": "GATE-READER-01"}
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "ALREADY_CHECKED_IN"

    # 3. Unknown card -> 404
    res_unk = client.post(
        "/api/attendance/rfid",
        json={"rfid_uid": "UNKNOWN-CARD-999"}
    )
    assert res_unk.status_code == 404

    # 4. Check ledger
    ledger_res = client.get(
        "/api/daily-checkins",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert ledger_res.status_code == 200
    logs = ledger_res.json()
    assert len(logs) >= 1
    assert any(log["rfid_uid"] == "TEST-UID-101" for log in logs)

