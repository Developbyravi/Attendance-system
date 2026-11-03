# SmartAttend AIoT Backend2 — Complete Architecture & Execution Guide

SmartAttend Backend2 is a completely re-engineered, enterprise-grade Python FastAPI backend designed for automated multi-face classroom attendance verification and physical RFID tap logging.

It runs independently on **port 8002**, preserving the legacy `backend/` directory 100% untouched.

---

## 1. Key Architectural Features

- **Decoupled 2-Layer Attendance Engine**:
  - **Layer 1 (Morning Gate RFID)**: Physical RFID tap logged via `POST /api/attendance/rfid` once per student per day. Idempotent against accidental double-taps.
  - **Layer 2 (Per-Lecture AI Face Verification)**: Teacher captures a classroom photograph. InsightFace SCRFD-10G detects all visible faces down to back-row students, aligns landmarks, and ArcFace-MobileFaceNet matches 512-D normalized embeddings against enrolled division students.
  - **Cross-Verification Matrix**:
    - **PRESENT**: RFID Morning Tap + AI Classroom Detection.
    - **FLAGGED (AI_ONLY)**: Visible in class, missed morning RFID.
    - **FLAGGED (RFID_ONLY)**: RFID tap present, not visible in photo.
    - **FLAGGED (AMBIGUOUS_AI)**: Multiple candidates match within 0.08 similarity margin; teacher review card surfaces one-click resolution.
    - **PENDING**: Undetected students remain pending during active lectures (never prematurely marked absent from a single photo).
    - **FINALIZED_ABSENT**: On lecture finalization, remaining pending records transition to absent and the session becomes immutable.
- **Enterprise Face AI Pipeline**:
  - InsightFace SCRFD-10G ONNX model with Feature Pyramid Network (strides 8, 16, 32).
  - Overlapping tiled window inference for ultra-high-resolution classroom photographs.
  - 5-point facial landmark affine alignment to standard 112x112 ArcFace template.
  - ArcFace 512-dimensional L2-normalized floating point vector embeddings ($||\vec{v}||_2 = 1.0$).
  - Consolidated person matching logic (prevents multi-enrollment duplicate accounts of the same student from declaring ambiguity against themselves).
- **Security & Authorization**:
  - Role-based authorization (`ADMIN`, `TEACHER`, `STUDENT`, `PARENT`).
  - Native Bcrypt password hashing and signed HS256 JWT tokens.
  - Compatible with Supabase PostgreSQL and local SQLite fallback.

---

## 2. Directory Structure

```text
backend2/
├── app/
│   ├── main.py                     # FastAPI application entrypoint & lifecycle
│   ├── config.py                   # Pydantic v2 settings & environment validation
│   ├── database.py                 # SQLAlchemy 2.0 engine, SessionLocal & schema init
│   ├── dependencies.py             # Dependency injection exports
│   ├── core/
│   │   ├── security.py             # Bcrypt hashing & PyJWT token management
│   │   ├── permissions.py          # Role enforcement & current user dependencies
│   │   ├── exceptions.py           # Domain HTTP exceptions
│   │   └── logging.py              # Structured console & rotating file logging
│   ├── models/                     # Normalized SQLAlchemy models
│   │   ├── user.py                 # UserModel
│   │   ├── teacher.py              # TeacherModel
│   │   ├── student.py              # StudentModel
│   │   ├── class_division.py       # ClassDivisionModel
│   │   ├── subject.py              # SubjectModel
│   │   ├── lecture.py              # LectureSessionModel
│   │   ├── daily_checkin.py        # DailyCheckinModel
│   │   ├── attendance.py           # LectureAttendanceModel, DeviceModel
│   │   └── face_embedding.py       # FaceEmbeddingModel
│   ├── schemas/                    # Pydantic v2 request/response schemas
│   │   ├── auth.py, user.py, student.py, teacher.py, lecture.py, attendance.py, etc.
│   ├── services/                   # Core business logic domain services
│   │   ├── rfid_service.py         # Daily RFID & interactive card assignment
│   │   ├── attendance_service.py   # AI + RFID Cross-Verification Matrix & Review
│   │   ├── student_service.py      # Student CRUD & biometric enrollment
│   │   ├── teacher_service.py      # Faculty management
│   │   ├── lecture_service.py      # Lecture session lifecycle
│   │   ├── storage_service.py      # Local & cloud photo storage
│   │   └── dashboard_service.py    # Analytics & overview KPIs
│   ├── routers/                    # FastAPI APIRouters under /api
│   │   ├── auth.py, students.py, teachers.py, lectures.py, attendance.py, rfid.py, portal.py, health.py
│   ├── ai/                         # Computer Vision & Deep Learning Subsystem
│   │   ├── detector.py             # SCRFD-10G ONNX Runtime Detector & Tiled Inference
│   │   ├── embedding.py            # ArcFace-MobileFaceNet 512-D Embedder
│   │   ├── matching.py             # Disambiguated Cosine Similarity Matching Engine
│   │   ├── preprocessing.py        # Letterbox padding & 5-point landmark affine aligner
│   │   └── recognizer.py           # Unified FaceRecognitionPipeline coordinator
│   └── utils/
│       └── image_utils.py          # Color-coded detection bounding box renderer
├── weights/
│   └── scrfd_10g_bnkps.onnx        # InsightFace SCRFD-10G ONNX model weights
├── scripts/
│   ├── seed_demo_data.py           # Seeds Admin, Teacher, Division A, and Ravi Khile
│   └── run_server.py               # Starts uvicorn server on port 8002
├── tests/                          # 100% Passing Automated Pytest Suite (19/19)
│   ├── conftest.py                 # Test fixtures & isolated SQLite database
│   ├── test_database.py            # Database CRUD tests
│   ├── test_auth.py                # Authentication & role permissions tests
│   ├── test_rfid.py                # Daily RFID tap & idempotency tests
│   ├── test_face_detection.py      # SCRFD-10G detection & letterboxing tests
│   ├── test_face_recognition.py    # ArcFace normalization & disambiguation tests
│   ├── test_attendance.py          # Lecture lifecycle & finalization immutability tests
│   └── api/
│       └── test_endpoints.py       # End-to-end API integration tests
├── requirements.txt
├── .env.example
├── pytest.ini
├── PROJECT_ANALYSIS.md
├── API_DOCUMENTATION.md
└── FINAL_REPORT.md
```

---

## 3. Quick Start & Execution

### 1. Install Dependencies
```powershell
pip install -r backend2/requirements.txt
```

### 2. Seed Default Database
```powershell
cd backend2
python scripts/seed_demo_data.py
```
This provisions:
- Administrator: `admin@smartattend.edu` / `Admin@123`
- Faculty Member: `teacher@smartattend.edu` / `Teacher@123`
- Student: `Ravi Khile` (Roll `10`, Division `A`, RFID UID `4847B047`)

### 3. Start Development Server
```powershell
cd backend2
uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
```

### 4. Interactive Documentation
- **Swagger UI**: [http://127.0.0.1:8002/docs](http://127.0.0.1:8002/docs)
- **ReDoc**: [http://127.0.0.1:8002/redoc](http://127.0.0.1:8002/redoc)
- **Health Diagnostics**: [http://127.0.0.1:8002/api/health](http://127.0.0.1:8002/api/health)

---

## 4. Running the Automated Test Suite

```powershell
python -m pytest backend2/tests -v
```
All 19 tests will execute against an isolated test database and verify:
- Authentication & JWT token generation
- Role-based route guards
- Campus RFID daily check-in & duplicate suppression
- SCRFD-10G model loading, aspect-ratio letterboxing, and landmarks extraction
- ArcFace 512-D L2-normalization & Cosine Similarity matching
- Lecture scheduling, review roster, flag resolution, and finalization immutability

