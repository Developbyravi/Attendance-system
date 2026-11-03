# SmartAttend — REST API Specification

**Base URL (Local)**: `http://localhost:8002/api`  
**Base URL (Production)**: `https://api.YOUR_DOMAIN.com/api`  
**Interactive Swagger UI**: `/docs`  
**ReDoc Specification**: `/redoc`  

---

## 1. Authentication Endpoints

### `POST /api/auth/token`
FastAPI OAuth2-compliant login endpoint.
- **Request Format**: `application/x-www-form-urlencoded`
- **Fields**:
  - `username` (string, required): Student roll number, employee ID, or institutional email.
  - `password` (string, required): Account password.
- **Response** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer"
  }
  ```

### `GET /api/auth/me`
Retrieves currently authenticated user profile.
- **Headers**: `Authorization: Bearer <token>`
- **Response** (`200 OK`):
  ```json
  {
    "id": 1,
    "username": "TCH-001",
    "email": "teacher@smartattend.edu",
    "full_name": "Prof. Sharma",
    "role": "teacher",
    "is_active": true,
    "student_id": null,
    "class_name": "Div A",
    "division": "A"
  }
  ```

### `POST /api/auth/register`
Unified registration endpoint. Public self-registration is strictly restricted to students.
- **Request Format**: `application/json`
- **Fields**:
  ```json
  {
    "email": "new.student@smartattend.edu",
    "password": "SecurePassword123!",
    "name": "Jane Doe",
    "roll_no": "STU-2026-001",
    "role": "STUDENT",
    "department": "Computer Science & Engineering",
    "year": "3rd Year",
    "division": "A"
  }
  ```
- **Response** (`200 OK`): Token response. Creating `TEACHER` or `ADMIN` accounts requires an Admin Bearer token; unauthenticated requests return `403 Forbidden`.

---

## 2. Hardware RFID & Kiosk Endpoints

### `POST /api/attendance/rfid` & `POST /api/kiosk/scan`
Physical campus entrance / kiosk card tap ingestion. Idempotent: repeated scans on the same calendar day return `ALREADY_CHECKED_IN`.
- **Request Format**: `application/json`
- **Fields**:
  ```json
  {
    "rfid_uid": "4847B047",
    "device_id": "GATE-READER-01"
  }
  ```
- **Response (New Daily Check-in — 200 OK)**:
  ```json
  {
    "status": "SUCCESS",
    "message": "Daily RFID check-in verified for 'Ravi Khile'.",
    "student": {
      "id": 1,
      "name": "Ravi Khile",
      "roll_number": "10",
      "division_name": "A",
      "department": "Computer Science & Engineering"
    },
    "check_in_time": "2026-11-03T07:48:57.000Z",
    "date": "2026-11-03"
  }
  ```
- **Response (Duplicate Scan — 200 OK)**:
  ```json
  {
    "status": "ALREADY_CHECKED_IN",
    "message": "Student 'Ravi Khile' has already checked in for today.",
    "student": { ... },
    "check_in_time": "2026-11-03T07:48:57.000Z",
    "date": "2026-11-03"
  }
  ```

---

## 3. Lecture & Classroom Attendance Endpoints

### `POST /api/lectures`
Creates a scheduled lecture session.
- **Headers**: `Authorization: Bearer <teacher_token>`
- **Request Format**: `application/json`
- **Fields**:
  ```json
  {
    "subject": "Internet of Things",
    "title": "Edge AI & Smart Attendance Architecture",
    "division": "A",
    "division_id": "A",
    "lecture_date": "2026-11-03",
    "start_time": "11:30",
    "classroom": "Lab-IoT-1"
  }
  ```

### `POST /api/lectures/{id}/photo`
Uploads raw classroom photograph and triggers AI detection, embedding extraction, and RFID cross-verification.
- **Headers**: `Authorization: Bearer <teacher_token>`
- **Request Format**: `multipart/form-data`
- **Fields**: `file`: Image file (JPEG/PNG)
- **Response** (`200 OK`):
  ```json
  {
    "lecture_id": 3,
    "subject": "Internet of Things",
    "division": "A",
    "date": "2026-11-03",
    "daily_rfid_checked_in": 1,
    "ai_detected_count": 1,
    "verified_present": 1,
    "rfid_only": 0,
    "ai_only": 0,
    "absent": 0,
    "pending": 1,
    "photo_url": "/uploads/classroom/lecture_3_raw.jpg",
    "overlay_image_url": "/uploads/classroom/lecture_3_overlay.jpg",
    "detected_faces": 1,
    "detector": "InsightFace SCRFD-10G",
    "attendances": [ ... ]
  }
  ```

### `GET /api/lectures/{id}/review`
Returns detailed student roster with RFID status, AI confidence score, and current attendance status.

### `PATCH /api/lectures/{id}/students/{student_id}`
Teacher manual override of student attendance status.
- **Headers**: `Authorization: Bearer <teacher_token>`
- **Request Format**: `application/json`
- **Fields**:
  ```json
  {
    "status": "PRESENT",
    "reason": "Teacher confirmed physical presence in Lab-IoT-1"
  }
  ```

### `POST /api/lectures/{id}/finalize`
Engages permanent immutable database lock on attendance records.
- **Headers**: `Authorization: Bearer <teacher_token>`
- **Business Invariant**: Unreviewed pending students remain `PENDING`; only confirmed absences become `ABSENT`. Post-finalization mutations return `400 Bad Request`.
- **Response** (`200 OK`):
  ```json
  {
    "finalized": true,
    "finalized_at": "2026-11-03T07:48:57.123456Z",
    "total_records": 2,
    "present_count": 1,
    "absent_count": 0,
    "pending_count": 1
  }
  ```

---

## 4. Student & Academic Portal Endpoints

- `GET /api/student/me/profile`: Authenticated student profile and biometric enrollment status.
- `GET /api/student/{id}/stats`: Summary statistics (attendance percentage, total lectures, present, absent, today RFID status, recent history).
- `POST /api/students/{id}/face-enroll`: Face biometric enrollment for student.
- `GET /api/classes`: List academic divisions and departments.
- `GET /api/devices`: List registered IoT hardware devices.
- `GET /api/admin/stats`: Institutional KPI metrics for admin overview.
