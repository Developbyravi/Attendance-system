# SmartAttend AIoT Backend2 — Complete API Specification
## Version 2.0.0 — OpenAPI Compliant REST API

Base URL: `http://localhost:8002/api`  
Interactive Documentation: `http://localhost:8002/docs` (Swagger UI) & `http://localhost:8002/redoc` (ReDoc)

---

### Table of Contents
1. [Authentication Endpoints](#1-authentication-endpoints)
2. [Student Management Endpoints](#2-student-management-endpoints)
3. [Teacher Management Endpoints](#3-teacher-management-endpoints)
4. [Classes & Divisions Endpoints](#4-classes--divisions-endpoints)
5. [IoT Devices & Kiosk Endpoints](#5-iot-devices--kiosk-endpoints)
6. [Daily RFID Check-In Endpoints](#6-daily-rfid-check-in-endpoints)
7. [Lecture Management Endpoints](#7-lecture-management-endpoints)
8. [Face Biometrics & Enrollment Endpoints](#8-face-biometrics--enrollment-endpoints)
9. [Dashboard & Statistics Endpoints](#9-dashboard--statistics-endpoints)
10. [Health & Diagnostics Endpoints](#10-health--diagnostics-endpoints)

---

### 1. Authentication Endpoints

#### 1.1 OAuth2 Login Token
- **POST** `/auth/token`
- **Auth**: None (Public)
- **Content-Type**: `application/x-www-form-urlencoded`
- **Request Body**:
  - `username` (string, required): Student roll number, teacher employee ID, or user email.
  - `password` (string, required): Plaintext password.
- **Success Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer"
  }
  ```
- **Error Responses**:
  - `401 Unauthorized`: `{"detail": "Invalid credentials or account inactive"}`
  - `422 Unprocessable Entity`: Field validation error.

#### 1.2 User Registration
- **POST** `/auth/register`
- **Auth**: Public or Admin
- **Request Body (JSON)**:
  ```json
  {
    "role": "student | teacher | admin | parent",
    "name": "Full Name",
    "email": "user@smartattend.edu",
    "password": "SecurePassword123!",
    "roll_no": "10",
    "department": "Computer Science & Engineering",
    "year": "3rd Year",
    "division": "A",
    "phone": "+919876543210"
  }
  ```
- **Success Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer"
  }
  ```
- **Error Responses**:
  - `400 Bad Request`: `{"detail": "Email or Roll Number already registered"}`

#### 1.3 Current User Info
- **GET** `/auth/me`
- **Auth**: Bearer Token
- **Success Response (200 OK)**:
  ```json
  {
    "id": 1,
    "username": "khileravi207@gmail.com",
    "email": "khileravi207@gmail.com",
    "full_name": "Ravi Khile",
    "role": "student",
    "is_active": true,
    "student_id": "10",
    "class_name": "Div A",
    "division": "A"
  }
  ```
- **Error Responses**:
  - `401 Unauthorized`: Token expired or missing.

---

### 2. Student Management Endpoints

#### 2.1 List Students
- **GET** `/students`
- **Auth**: Bearer Token (`TEACHER` or `ADMIN`)
- **Query Parameters**:
  - `division_id` (string, optional): Filter by division code or ID.
  - `q` (string, optional): Search by name, roll number, or email.
- **Success Response (200 OK)**: Array of `StudentRecord`.

#### 2.2 Create Student
- **POST** `/students`
- **Auth**: Bearer Token (`ADMIN`)
- **Request Body**:
  ```json
  {
    "roll_no": "10",
    "name": "Ravi Khile",
    "email": "khileravi207@gmail.com",
    "department": "Computer Science & Engineering",
    "year": "3rd Year",
    "division": "A",
    "rfid_uid": "4847B047"
  }
  ```
- **Success Response (201 Created)**: Created `StudentRecord`.

#### 2.3 Student Self Profile
- **GET** `/student/me/profile`
- **Auth**: Bearer Token (`STUDENT`)
- **Success Response (200 OK)**:
  ```json
  {
    "id": 303,
    "name": "Ravi Khile",
    "roll_no": "10",
    "email": "khileravi207@gmail.com",
    "department": "Computer Science & Engineering",
    "year": "3rd Year",
    "division": "A",
    "rfid_uid": "4847B047",
    "face_enrolled": true,
    "created_at": "2026-10-13T09:58:22Z"
  }
  ```

---

### 3. Daily RFID Check-In Endpoints

#### 3.1 Campus RFID Check-In (Canonical)
- **POST** `/attendance/rfid`
- **Auth**: None / Device API Key
- **Request Body**:
  ```json
  {
    "rfid_uid": "4847B047",
    "device_id": "GATE-READER-01"
  }
  ```
- **Success Response (200 OK - First Check-in)**:
  ```json
  {
    "status": "SUCCESS",
    "message": "Daily check-in verified successfully",
    "student": {
      "id": 303,
      "name": "Ravi Khile",
      "roll_number": "10",
      "division_name": "A",
      "department": "Computer Science & Engineering"
    },
    "check_in_time": "2026-11-03T08:45:12Z",
    "date": "2026-11-03"
  }
  ```
- **Success Response (200 OK - Duplicate Same Day)**:
  ```json
  {
    "status": "ALREADY_CHECKED_IN",
    "message": "Student has already checked in for today",
    "student": {
      "id": 303,
      "name": "Ravi Khile",
      "roll_number": "10",
      "division_name": "A"
    },
    "check_in_time": "2026-11-03T08:45:12Z"
  }
  ```
- **Error Response (404 Not Found)**:
  `{"detail": "Unrecognized RFID card. Please register this card with an active student."}`

#### 3.2 List Daily Check-Ins
- **GET** `/daily-checkins`
- **Auth**: Bearer Token (`TEACHER` or `ADMIN`)
- **Query Parameters**:
  - `division_id` (string, optional)
  - `date` (YYYY-MM-DD, optional, defaults to today)
- **Success Response (200 OK)**: Array of `DailyCheckInRecord`.

---

### 4. Lecture Management & AI Attendance Endpoints

#### 4.1 Schedule / Create Lecture Session
- **POST** `/lectures`
- **Auth**: Bearer Token (`TEACHER`)
- **Request Body**:
  ```json
  {
    "subject": "Deep Learning & Neural Networks",
    "title": "CNNs & Object Detection",
    "division_id": "A",
    "division": "A",
    "lecture_date": "2026-11-03",
    "start_time": "10:00",
    "classroom": "Room 402"
  }
  ```
- **Success Response (201 Created)**: Created `LectureSession`.

#### 4.2 Process Classroom Photograph (Layer 2 AI Cross-Verification)
- **POST** `/lectures/{lecture_id}/photo`
- **Auth**: Bearer Token (`TEACHER`)
- **Content-Type**: `multipart/form-data`
- **Form Data**:
  - `file` or `photo` (File binary, JPEG/PNG image)
  - `threshold` (float query, default `0.70`)
  - `auto_mark_absent` (bool query, default `false`)
- **Pipeline Execution**:
  1. Image validation & aspect-ratio normalization.
  2. InsightFace SCRFD-10G inference for bounding boxes and 5 facial landmarks.
  3. Landmark affine face alignment to 112x112 template.
  4. ArcFace-MobileFaceNet 512-D L2-normalized feature vector generation.
  5. Cosine similarity candidate evaluation against enrolled students in this lecture's division.
  6. Ambiguity evaluation (margin < 0.08) and automatic RFID resolution if available.
  7. Cross-referencing against today's Daily RFID check-ins.
  8. Generation of visual annotated overlay with color-coded bounding boxes.
- **Success Response (200 OK)**:
  ```json
  {
    "lecture_id": 527,
    "subject": "Deep Learning & Neural Networks",
    "division": "A",
    "date": "2026-11-03",
    "daily_rfid_checked_in": 1,
    "ai_detected_count": 1,
    "verified_present": 1,
    "rfid_only": 0,
    "ai_only": 0,
    "absent": 0,
    "pending": 0,
    "unknown_faces": 0,
    "detected_faces": 1,
    "detector": "InsightFace SCRFD-10G",
    "photo_url": "/uploads/classroom/lecture_527_raw.jpg",
    "overlay_image_url": "/uploads/classroom/lecture_527_annotated.jpg",
    "detected_boxes": [
      {
        "bbox": [474, 235, 325, 428],
        "detector_confidence": 0.799,
        "similarity": 0.857,
        "match_status": "recognized",
        "student_id": 303,
        "student_name": "Ravi Khile",
        "roll_no": "10"
      }
    ],
    "attendances": [ ... ]
  }
  ```

#### 4.3 Teacher Review Roster
- **GET** `/lectures/{lecture_id}/review`
- **Auth**: Bearer Token (`TEACHER`)
- **Success Response (200 OK)**: Array of `AttendanceReviewItem` with competing candidates for flagged rows.

#### 4.4 Override Student Attendance
- **PATCH** `/lectures/{lecture_id}/students/{student_id}`
- **Auth**: Bearer Token (`TEACHER`)
- **Request Body**:
  ```json
  {
    "status": "PRESENT | ABSENT | FLAGGED",
    "reason": "Teacher verified physical presence in row 2"
  }
  ```
- **Success Response (200 OK)**: Updated attendance item.

#### 4.5 Finalize Lecture Attendance (Immutability Lock)
- **POST** `/lectures/{lecture_id}/finalize`
- **Auth**: Bearer Token (`TEACHER`)
- **Success Response (200 OK)**:
  ```json
  {
    "finalized": true,
    "finalized_at": "2026-11-03T11:15:00Z",
    "total_records": 60,
    "present_count": 52,
    "absent_count": 8
  }
  ```
- **Rule**: Once finalized, any subsequent modification attempts return `400 Bad Request ("Lecture session is finalized and immutable")`.

---

### 5. Health & Diagnostics Endpoint

#### 5.1 System Health
- **GET** `/health`
- **Auth**: None (Public)
- **Success Response (200 OK)**:
  ```json
  {
    "status": "healthy",
    "app_name": "SmartAttend AIoT Backend2",
    "version": "2.0.0",
    "database": {
      "engine": "sqlite | postgresql",
      "connected": true
    },
    "ai_engine": {
      "detector": "InsightFace SCRFD-10G",
      "detector_loaded": true,
      "device": "CPUExecutionProvider",
      "recognition_model": "ArcFace-MobileFaceNet",
      "embedding_dimension": 512,
      "recognition_threshold": 0.70,
      "ambiguity_threshold": 0.08
    },
    "storage": {
      "driver": "local | supabase",
      "writable": true
    }
  }
  ```

