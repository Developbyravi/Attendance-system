# AIoT SmartAttend — FastAPI Backend Microservice (v2.0)

Production-grade FastAPI backend for **AIoT SmartAttend** integrating **YOLOv11n-face** detection, **ArcFace 512-d** facial recognition, **Supabase** (PostgreSQL, Storage, Auth JWT, RLS), and dual-verification cross-referencing (Campus Daily RFID + Classroom AI Face Recognition).

---

## 🛠️ Architecture & System Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI application, CORS middleware, router aggregation
│   ├── config.py                # Environment configuration (Pydantic BaseSettings)
│   ├── database.py              # SQLAlchemy engine & SQLite / PostgreSQL session setup
│   ├── core/
│   │   └── security.py          # JWT Auth, password hashing, Supabase token decoder & RBAC
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── student.py           # StudentModel
│   │   ├── teacher.py           # TeacherModel
│   │   ├── parent.py            # ParentModel & ParentStudentModel
│   │   ├── daily_checkin.py     # DailyCheckinModel (RFID ingress)
│   │   ├── lecture_session.py   # LectureSessionModel
│   │   ├── lecture_attendance.py# LectureAttendanceModel (per-student verification)
│   │   ├── face_embedding.py    # FaceEmbeddingModel (512-d ArcFace vector storage)
│   │   └── audit_log.py         # AuditLogModel (event logging & immutability audit)
│   ├── schemas/                 # Pydantic v2 schemas
│   │   ├── auth.py              # Login, registration, token schemas
│   │   ├── student.py           # Student CRUD schemas
│   │   ├── daily_checkin.py     # Daily RFID check-in schemas
│   │   ├── lecture.py           # Lecture creation, verification summary, review schemas
│   │   └── face.py              # Face enrollment & model metadata schemas
│   ├── routers/                 # API endpoint routers
│   │   ├── health.py            # GET /health, GET /api/health
│   │   ├── auth.py              # POST /api/auth/token, /register, GET /me
│   │   ├── students.py          # Student CRUD, face enrollment, deactivation
│   │   ├── attendance.py        # POST /api/attendance/rfid, GET /daily-checkins
│   │   ├── lectures.py          # Lecture lifecycle, photo upload, flag resolution, finalization
│   │   ├── student_portal.py    # GET /api/student/me/profile, /attendance
│   │   ├── portal_api.py        # Dashboard stats, classes, teachers, kiosk endpoints
│   │   └── ai.py                # GET /api/ai/model-info
│   └── services/                # Decoupled vision, embedding, and cloud services
│       ├── face_detector.py     # YOLOv11n-face singleton (Ultralytics) + Haar fallback
│       ├── face_recognition.py  # Face matching, ambiguity detection, cosine similarity
│       ├── face_embedding.py    # ArcFace 512-d embedder
│       ├── image_processor.py   # Image decoding, validation, cropping & alignment
│       ├── verification_engine.py # Stage 3 cross-verification decision matrix
│       └── supabase_service.py  # Supabase client, storage buckets, audit logger, fallback
├── migrations/
│   └── 001_initial_supabase_schema.sql # Complete Supabase PostgreSQL schema, RLS, storage
├── scripts/
│   ├── download_weights.py      # Automated YOLOv11n-face weights downloader & hash checker
│   └── reset_database.py        # Explicit database reset script
├── weights/
│   └── yolov11n-face.pt         # Pretrained YOLOv11n-face weights (5.45 MB)
├── tests/                       # 31 automated test cases (100% passing)
│   ├── test_advanced_face_and_supabase.py
│   ├── test_auth.py
│   ├── test_classroom_verification.py
│   ├── test_cross_verification.py
│   ├── test_daily_lecture_attendance.py
│   ├── test_health.py
│   ├── test_portal_and_dashboard_api.py
│   ├── test_students.py
│   └── test_yolo_face_detector.py
├── .env.example
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Start & Installation

### 1. Python Environment Setup
Ensure Python 3.11 or 3.12 is installed:

```bash
cd backend
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Download Model Weights
Run the automated downloader to fetch `yolov11n-face.pt` directly from GitHub releases:

```bash
python scripts/download_weights.py
```
*Weights file will be placed in `backend/weights/yolov11n-face.pt` (Size: ~5.45 MB).*

Manual download alternative:
```bash
# Windows PowerShell
Invoke-WebRequest -Uri "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11n-face.pt" -OutFile "weights/yolov11n-face.pt"

# Linux / curl
curl -L -o weights/yolov11n-face.pt "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11n-face.pt"
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in credentials:

```bash
cp .env.example .env
```

Key environment settings:
| Variable | Default / Placeholder | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./smartattend.db` | PostgreSQL or local SQLite URL |
| `SUPABASE_URL` | `https://your-project.supabase.co` | Supabase API URL |
| `SUPABASE_KEY` | `your-anon-or-service-role-key` | Supabase Service Role Key |
| `SUPABASE_JWT_SECRET` | `your-supabase-jwt-secret` | Supabase JWT Secret for token verification |
| `YOLO_FACE_MODEL_PATH` | `weights/yolov11n-face.pt` | Path to YOLO face model weights |
| `YOLO_CONF_THRESHOLD` | `0.40` | Face detection bounding box threshold |
| `FACE_RECOGNITION_THRESHOLD` | `0.70` | ArcFace cosine similarity threshold |
| `FACE_AMBIGUITY_THRESHOLD` | `0.08` | Threshold difference between top-1 and top-2 candidates |

### 4. Running the Server

Development mode with hot reloading:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Production mode (multi-worker):
```bash
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8001
```

Access Swagger UI: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## 🗄️ Supabase PostgreSQL Migration Instructions

To apply the complete PostgreSQL database schema, Row-Level Security (RLS) policies, and storage bucket configuration:

1. Open your **Supabase Dashboard** -> **SQL Editor**.
2. Create a **New query**.
3. Open `backend/migrations/001_initial_supabase_schema.sql`.
4. Copy the entire file content and paste it into the Supabase SQL Editor.
5. Click **Run**.
6. The migration script executes idempotently:
   - Creates tables: `divisions`, `teachers`, `students`, `parents`, `parent_students`, `face_embeddings`, `daily_checkins`, `lecture_sessions`, `lecture_attendances`, `audit_logs`.
   - Creates performance indexes on student roll numbers, RFID UIDs, lecture session dates, and student IDs.
   - Enables RLS on all tables with granular policies for `TEACHER`, `STUDENT`, `ADMIN`, and `PARENT`.
   - Configures Supabase Storage buckets `student-enrollments` and `classroom-images`.

---

## 🧪 Automated Testing

Run the full pytest suite (31 comprehensive unit and integration tests):

```bash
pytest -v
```

All 31 tests pass with 100% reliability:
- `test_yolo_face_detector.py`: Singleton lazy loading, blank image rejection, oversized dimension downscaling, multi-face real image detection.
- `test_advanced_face_and_supabase.py`: Ambiguity detection (<0.08 diff), multi-detection deduplication, inactive RFID rejection, finalized immutability, role isolation, Supabase offline fallback.
- `test_portal_and_dashboard_api.py`: Kiosk status, live scan & duplicate detection, device inventory, teacher and class rosters, administrative metrics, student analytics, review roster, manual overrides.
- `test_cross_verification.py`: Full Stage 3 cross-verification decision matrix.
- `test_classroom_verification.py`: Zero faces handling, configurable thresholds.
- `test_daily_lecture_attendance.py`: Daily check-in, division filtering, student portal access.
- `test_auth.py` & `test_students.py`: RBAC authentication and student enrollment pipelines.

---

## ⚖️ Verification Decision Matrix

| RFID Checked-in | AI Detected | Initial Status | Teacher Review | Final State |
|---|---|---|---|---|
| **Yes** | **Yes** (score >= 0.70) | `PRESENT` | Not required | Verified Present |
| **Yes** | **No** | `FLAGGED` (`RFID_ONLY`) | Required (`CONFIRM_PRESENT` / `MARK_ABSENT`) | Teacher Confirmed / Absent |
| **No** | **Yes** (score >= 0.70) | `FLAGGED` (`AI_ONLY`) | Required (`CONFIRM_PRESENT` / `MARK_ABSENT`) | Teacher Confirmed / Absent |
| **No** | **No** | `ABSENT` | Default | Verified Absent |

*Attendance is **never auto-finalized**. A faculty member must resolve all flags and finalize the session before attendance becomes cryptographically locked and immutable.*

---

## 📜 Model Licensing Notes

- **YOLOv11n-face**: The underlying YOLOv11 model is developed by Ultralytics and distributed under the **AGPL-3.0** open-source license.
- **Commercial Use**: For commercial enterprise deployments that cannot adhere to AGPL-3.0 open-source requirements, an Ultralytics Enterprise License must be acquired.
- **Weights Attribution**: Pretrained weights ported by [akanametov/yolo-face](https://github.com/akanametov/yolo-face).
