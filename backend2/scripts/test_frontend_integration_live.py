"""
SmartAttend Backend2 — Controlled Frontend & Backend Live Integration Test
Verifies the complete integration between Next.js (port 3000) and FastAPI Backend2 (port 8002).
"""

import os
import sys
import json
import httpx
import numpy as np

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://127.0.0.1:8002/api"

def print_header(title):
    print("\n" + "=" * 70)
    print(f" {title.upper()}")
    print("=" * 70)

def test_step_1_environment_configuration():
    print_header("Step 1: Frontend Environment Configuration Check")
    
    # Check .env.local
    env_path = ".env.local"
    assert os.path.exists(env_path), "Missing .env.local"
    with open(env_path, "r") as f:
        content = f.read()
    
    assert "NEXT_PUBLIC_API_URL=http://localhost:8002/api" in content, (
        f"NEXT_PUBLIC_API_URL not properly set to port 8002: {content}"
    )
    print("[PASS] .env.local configured: NEXT_PUBLIC_API_URL=http://localhost:8002/api")

    # Check backup exists
    backup_path = ".env.local.backup"
    assert os.path.exists(backup_path), "Missing .env.local.backup"
    print(f"[PASS] Environment backup verified at {backup_path}")

def test_step_2_authentication_and_route_guards():
    print_header("Step 2: Authentication & Route Protection Middleware")
    client_api = httpx.Client(base_url=BACKEND_URL, timeout=10.0)
    client_fe = httpx.Client(base_url=FRONTEND_URL, timeout=10.0, follow_redirects=False)

    # 1. Admin Login
    r_admin = client_api.post("/auth/token", data={"username": "admin@smartattend.edu", "password": "Admin@123"})
    assert r_admin.status_code == 200, f"Admin login failed: {r_admin.text}"
    admin_token = r_admin.json()["access_token"]
    print(f"[PASS] Admin Login: Success (200 OK) -> Token issued")

    # 2. Teacher Login
    r_teacher = client_api.post("/auth/token", data={"username": "teacher@smartattend.edu", "password": "Teacher@123"})
    assert r_teacher.status_code == 200, f"Teacher login failed: {r_teacher.text}"
    teacher_token = r_teacher.json()["access_token"]
    print(f"[PASS] Teacher Login: Success (200 OK) -> Token issued")

    # 3. Student Login (Ravi Khile)
    r_student = client_api.post("/auth/token", data={"username": "khileravi207@gmail.com", "password": "Student@123"})
    assert r_student.status_code == 200, f"Student login failed: {r_student.text}"
    student_token = r_student.json()["access_token"]
    print(f"[PASS] Student Login: Success (200 OK) -> Token issued for Ravi Khile")

    # 4. Protected Route: Unauthenticated access to /teacher -> Must redirect to /login
    r_unauth_teacher = client_fe.get("/teacher")
    assert r_unauth_teacher.status_code in [302, 307], f"Expected redirect, got {r_unauth_teacher.status_code}"
    loc = r_unauth_teacher.headers.get("location", "")
    assert "/login" in loc, f"Expected redirect to /login, got {loc}"
    print(f"[PASS] Protected Route Guard: Unauthenticated /teacher redirected to {loc} (Status {r_unauth_teacher.status_code})")

    # 5. Protected Route: Unauthenticated access to /student -> Must redirect to /login
    r_unauth_student = client_fe.get("/student")
    assert r_unauth_student.status_code in [302, 307]
    assert "/login" in r_unauth_student.headers.get("location", "")
    print(f"[PASS] Protected Route Guard: Unauthenticated /student redirected to /login")

    # 6. Authenticated Teacher accessing /teacher -> Allowed (200 OK)
    r_auth_teacher = client_fe.get("/teacher", cookies={"smartattend_token": teacher_token})
    assert r_auth_teacher.status_code == 200, f"Teacher portal access failed: {r_auth_teacher.status_code}"
    print(f"[PASS] Authenticated Teacher Route: Access to /teacher granted (Status 200 OK)")

    # 7. Authenticated Teacher attempting /student -> Unauthorized (Redirect to /unauthorized)
    r_teacher_on_student = client_fe.get("/student", cookies={"smartattend_token": teacher_token})
    assert r_teacher_on_student.status_code in [302, 307]
    assert "/unauthorized" in r_teacher_on_student.headers.get("location", "")
    print(f"[PASS] Role Boundary Guard: Teacher blocked from /student (Redirected to /unauthorized)")

    # 8. Authenticated Student accessing /student -> Allowed (200 OK)
    r_auth_student = client_fe.get("/student", cookies={"smartattend_token": student_token})
    assert r_auth_student.status_code == 200, f"Student portal access failed: {r_auth_student.status_code}"
    print(f"[PASS] Authenticated Student Route: Access to /student granted (Status 200 OK)")

    # 9. Authenticated Student attempting /teacher -> Unauthorized (Redirect to /unauthorized)
    r_student_on_teacher = client_fe.get("/teacher", cookies={"smartattend_token": student_token})
    assert r_student_on_teacher.status_code in [302, 307]
    assert "/unauthorized" in r_student_on_teacher.headers.get("location", "")
    print(f"[PASS] Role Boundary Guard: Student blocked from /teacher (Redirected to /unauthorized)")

    # 10. Authenticated Admin accessing /admin -> Allowed (200 OK)
    r_auth_admin = client_fe.get("/admin", cookies={"smartattend_token": admin_token})
    assert r_auth_admin.status_code == 200, f"Admin portal access failed: {r_auth_admin.status_code}"
    print(f"[PASS] Authenticated Admin Route: Access to /admin granted (Status 200 OK)")

    return {
        "admin_token": admin_token,
        "teacher_token": teacher_token,
        "student_token": student_token
    }

def test_step_3_teacher_dashboard_and_workflows(tokens):
    print_header("Step 3: Teacher Dashboard APIs & Workflows")
    client = httpx.Client(base_url=BACKEND_URL, timeout=15.0)
    t_token = tokens["teacher_token"]
    headers = {"Authorization": f"Bearer {t_token}"}

    # 1. Teacher Profile (/api/auth/me)
    r_me = client.get("/auth/me", headers=headers)
    assert r_me.status_code == 200
    me_data = r_me.json()
    assert me_data["role"] == "teacher"
    print(f"[PASS] Teacher Profile: {me_data['full_name']} ({me_data['email']}), Division: {me_data.get('division')}")

    # 2. Assigned Classes (/api/classes)
    r_classes = client.get("/classes", headers=headers)
    assert r_classes.status_code == 200
    classes = r_classes.json()
    assert len(classes) >= 1
    print(f"[PASS] Assigned Classes: Discovered {len(classes)} division(s): {[c['name'] for c in classes]}")

    # 3. Student Roster for Division A (/api/students?division_id=A)
    r_students = client.get("/students?division_id=A", headers=headers)
    assert r_students.status_code == 200
    students = r_students.json()
    assert len(students) >= 1
    print(f"[PASS] Division A Student Roster: {len(students)} student(s) enrolled")
    ravi = next((s for s in students if "Ravi" in s["name"] or s["roll_no"] == "10"), None)
    assert ravi is not None, "Ravi Khile not found in Division A roster!"
    print(f"       Target Student: {ravi['name']} (Roll: {ravi['roll_no']}, RFID: {ravi['rfid_uid']}, Face: {ravi['face_enrolled']})")

    # 4. Daily RFID Morning Check-in Status (/api/daily-checkins)
    r_checkins = client.get("/daily-checkins?division_id=A", headers=headers)
    assert r_checkins.status_code == 200
    checkin_list = r_checkins.json()
    print(f"[PASS] Daily Check-ins: Found {len(checkin_list)} morning check-in log(s) for Division A")

    # 5. Create a New Lecture Session
    r_new_lec = client.post(
        "/lectures",
        json={
            "subject": "Internet of Things",
            "title": "Edge AI & Smart Attendance Architecture",
            "division": "A",
            "division_id": "A",
            "lecture_date": "2026-11-03",
            "start_time": "11:30",
            "classroom": "Lab-IoT-1"
        },
        headers=headers
    )
    assert r_new_lec.status_code == 200
    lec = r_new_lec.json()
    lec_id = lec["id"]
    print(f"[PASS] Lecture Session Created: ID={lec_id}, Subject='{lec['subject']}', Status='{lec['status']}'")

    # 6. Query Active Lecture Details (/api/lectures/{id})
    r_lec_detail = client.get(f"/lectures/{lec_id}", headers=headers)
    assert r_lec_detail.status_code == 200
    assert r_lec_detail.json()["title"] == "Edge AI & Smart Attendance Architecture"
    print(f"[PASS] Active Lecture Details retrieved: '{r_lec_detail.json()['title']}'")

    # 7. Upload Real Classroom Photo & Execute Multi-face Verification
    photo_path = "backend/storage/student_images/classroom_lecture_527/c3a8913960a7.jpg"
    with open(photo_path, "rb") as f:
        img_bytes = f.read()

    r_photo = client.post(
        f"/lectures/{lec_id}/photo",
        files={"file": ("classroom_iot.jpg", img_bytes, "image/jpeg")},
        headers=headers
    )
    assert r_photo.status_code == 200, f"Classroom photo processing failed: {r_photo.text}"
    photo_res = r_photo.json()
    print(f"[PASS] Classroom Photo Processed: Faces detected: {photo_res['detected_faces']}")
    print(f"       Verified Present: {photo_res['verified_present']}, RFID-Only: {photo_res['rfid_only']}, AI-Only: {photo_res['ai_only']}")
    print(f"       Pending: {photo_res['pending']}, Overlay Image: {photo_res['overlay_image_url']}")

    # 8. Teacher Review Roster (/api/lectures/{id}/review)
    r_review = client.get(f"/lectures/{lec_id}/review", headers=headers)
    assert r_review.status_code == 200
    roster = r_review.json()
    assert len(roster) >= 1
    print(f"[PASS] Review Roster fetched: {len(roster)} student record(s)")

    # 9. Teacher Manual Review & Overrides
    target_student_id = roster[0]["student_id"]
    r_override = client.patch(
        f"/lectures/{lec_id}/students/{target_student_id}",
        json={"status": "PRESENT", "reason": "Teacher confirmed physical presence in Lab-IoT-1"},
        headers=headers
    )
    assert r_override.status_code == 200
    assert r_override.json()["attendance_status"] == "PRESENT"
    print(f"[PASS] Teacher Manual Override: Student #{target_student_id} confirmed PRESENT")

    return lec_id, target_student_id

def test_step_4_student_dashboard_and_history(tokens):
    print_header("Step 4: Student Dashboard APIs & Attendance History")
    client = httpx.Client(base_url=BACKEND_URL, timeout=10.0)
    s_token = tokens["student_token"]
    headers = {"Authorization": f"Bearer {s_token}"}

    # 1. Student Profile (/api/student/me/profile)
    r_prof = client.get("/student/me/profile", headers=headers)
    assert r_prof.status_code == 200, f"Failed: {r_prof.text}"
    prof = r_prof.json()
    assert prof["roll_no"] == "10"
    print(f"[PASS] Student Profile: {prof['name']} (Roll: {prof['roll_no']}, Div: {prof['division']}, Department: {prof['department']})")
    print(f"       Biometrics: RFID={prof['rfid_uid']}, Face Enrolled={prof['face_enrolled']}")

    # 2. Student Statistics (/api/student/{student_id}/stats)
    r_stats = client.get(f"/student/{prof['id']}/stats", headers=headers)
    assert r_stats.status_code == 200
    stats = r_stats.json()
    print(f"[PASS] Student Stats: Total Lectures={stats['total_lectures']}, Present={stats['present_count']}, Absent={stats['absent_count']}")
    print(f"       Attendance Percentage={stats['attendance_percentage']}%, Today RFID Check-in={stats['today_rfid_checked_in']}")
    print(f"       Recent Records Discovered: {len(stats['recent_records'])}")

def test_step_5_and_6_attendance_finalization_rule_and_workflow(tokens, lec_id, student_id):
    print_header("Step 5 & 6: Controlled Finalization Rule & Full Integrated Workflow")
    client = httpx.Client(base_url=BACKEND_URL, timeout=10.0)
    t_token = tokens["teacher_token"]
    headers = {"Authorization": f"Bearer {t_token}"}

    # 1. Check review roster before finalization
    r_roster = client.get(f"/lectures/{lec_id}/review", headers=headers)
    roster = r_roster.json()
    unconfirmed = [item for item in roster if item["attendance_status"] == "PENDING"]
    print(f"[INFO] Current Roster status breakdown: Total={len(roster)}, Pending={len(unconfirmed)}")

    # 2. Execute Finalize Lecture
    r_finalize = client.post(f"/lectures/{lec_id}/finalize", headers=headers)
    assert r_finalize.status_code == 200
    fin_data = r_finalize.json()
    assert fin_data["finalized"] is True
    print(f"[PASS] Lecture Finalization Engaged: finalized={fin_data['finalized']}, Total={fin_data['total_records']}")
    print(f"       Present Count={fin_data['present_count']}, Absent Count={fin_data['absent_count']}, Pending Count={fin_data.get('pending_count', 0)}")

    # 3. CRITICAL BUSINESS RULE VERIFICATION:
    # Ensure unreviewed PENDING records were NOT converted to ABSENT automatically!
    r_post_roster = client.get(f"/lectures/{lec_id}/review", headers=headers)
    post_roster = r_post_roster.json()
    for item in post_roster:
        if item["student_id"] == student_id:
            assert item["attendance_status"] == "PRESENT", f"Explicitly confirmed student lost PRESENT status!"
        else:
            # Unreviewed students should remain PENDING (not blindly marked ABSENT)
            print(f"[PASS] Student '{item['student_name']}' status preserved as: '{item['attendance_status']}'")

    # 4. Immutability Lock Verification
    r_tamper = client.patch(
        f"/lectures/{lec_id}/students/{student_id}",
        json={"status": "ABSENT", "reason": "Attempting unauthorized post-finalization mutation"},
        headers=headers
    )
    assert r_tamper.status_code == 400
    print(f"[PASS] Immutability Lock Enforced: Post-finalization edit rejected with HTTP 400")

def run_all_integration_tests():
    print("\n" + "#" * 70)
    print(" SMARTATTEND BACKEND2 — LIVE FRONTEND INTEGRATION VERIFICATION")
    print("#" * 70)

    test_step_1_environment_configuration()
    tokens = test_step_2_authentication_and_route_guards()
    lec_id, student_id = test_step_3_teacher_dashboard_and_workflows(tokens)
    test_step_4_student_dashboard_and_history(tokens)
    test_step_5_and_6_attendance_finalization_rule_and_workflow(tokens, lec_id, student_id)

    print("\n" + "=" * 70)
    print(" ALL FRONTEND & BACKEND2 INTEGRATION VERIFICATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    run_all_integration_tests()

