# SmartAttend — AIoT Smart Attendance System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15.3.3-000000.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![ONNX Runtime](https://img.shields.io/badge/ONNX_Runtime-1.20+-005CED.svg?logo=onnx&logoColor=white)](https://onnxruntime.ai/)
[![Hardware](https://img.shields.io/badge/Hardware-ESP8266_%2B_RC522-E7352C.svg?logo=espressif&logoColor=white)](https://www.espressif.com/)

**Repository**: [https://github.com/Developbyravi/Attendance-system](https://github.com/Developbyravi/Attendance-system)

---

## 1. Project Overview

**SmartAttend** is an enterprise-grade AIoT (Artificial Intelligence of Things) automated attendance management system engineered for modern academic institutions. It deterministically eliminates proxy attendance and time-consuming roll calls by combining:

- **Perimeter Hardware Presence**: Morning gate / kiosk RFID tap via ESP8266 + MFRC522.
- **In-Classroom Edge AI Verification**: Single-photo classroom capture analyzed by **InsightFace SCRFD-10G ONNX** face detection and **ArcFace-MobileFaceNet 512-dimensional L2-normalized biometric embeddings**.
- **Dual-Layer Cross-Verification**: An automated cross-check matrix that corroborates classroom visual presence against morning campus physical arrival.
- **Human-in-the-Loop Teacher Supervision**: Unreviewed students are preserved in **`PENDING`** state (never blindly marked absent), allowing faculty to review annotated visual overlays, resolve flags, and commit an immutable finalized attendance record.
- **Role-Based Portals**: Dedicated, secured portals for Teachers, Students, Administrators, and Public Kiosks.

---

## 2. Problem Statement

Traditional attendance methods in university and enterprise environments suffer from severe structural vulnerabilities:
1. **Buddy Punching & Proxy Attendance**: Students sign attendance registers for absent peers or share credentials.
2. **Instructional Time Waste**: Calling rolls across 60–120 students consumes 10–15 minutes of every lecture hour.
3. **Data Fragmentation**: Campus gate check-ins (security) and classroom attendance (faculty) operate in disconnected silos without cross-verification.
4. **Lack of Immediate Transparency**: Students cannot view verified attendance metrics in real-time, leading to dispute over mandatory minimum attendance thresholds.

---

## 3. Project Objectives

- Provide instantaneous physical check-in at campus entryways via contactless RFID cards.
- Process dense classroom photos ($>50$ students) with sub-second deep learning face detection and keypoint alignment.
- Guarantee biometric data privacy by storing only non-invertible 512-D mathematical vectors instead of raw student facial images.
- Enforce strict data isolation and immutable audit logs for all attendance modifications.

---

## 4. Key Implemented Features

### Hardware & RFID Subsystem
- Contactless student identification using 13.56 MHz Mifare RFID cards.
- Sub-second ingestion via ESP8266 NodeMCU 12E Wi-Fi microcontroller.
- **Idempotency**: Automatic duplicate scan suppression within the same calendar day returning `ALREADY_CHECKED_IN`.
- **Dual-Mode Operation**: Seamless switching between regular Daily Check-in and Administrative Card Assignment mode without rebooting hardware.

### AI Vision & Biometrics Subsystem
- **InsightFace SCRFD-10G ONNX**: Multi-scale face detection across strides 8, 16, and 32 with 5-point facial landmark regression.
- **Affine Facial Alignment**: 5-point landmark warping to standard $112 \times 112 \times 3$ RGB crops.
- **ArcFace-MobileFaceNet**: Generates 512-dimensional L2-normalized feature vectors ($\|v\|_2 = 1.000000$).
- **Disambiguation Engine**: Resolves borderline face matches (<0.08 cosine similarity margin) using physical morning RFID presence.
- **Visual Detection Overlay**: Automatic generation of annotated bounding-box images showing verified, flagged, and unknown faces.

### Teacher & Faculty Portal
- Real-time dashboard showing today's RFID check-in count and assigned division registers.
- Lecture scheduling and active session room management.
- Single-click classroom photograph upload with live AI processing.
- Interactive attendance review roster with manual status overrides (`PRESENT`, `ABSENT`, `FLAGGED`).
- **Controlled Finalization Rule**: Preserves unreviewed students in `PENDING` status; only confirmed absences become `ABSENT`. Once finalized, sessions are permanently locked against post-session tampering.

### Student Self-Service Portal
- Student profile with registered RFID UID and face biometric enrollment status.
- Real-time overall and subject-wise attendance percentage tracking.
- Immediate morning RFID check-in verification timestamp.
- Detailed historical log of all attended and absent lectures.

---

## 5. System Architecture

```text
+-----------------------+              +-----------------------+
|  Student RFID Card    |              |   Classroom Camera    |
| (13.56 MHz Mifare)    |              |  (High-Res Image)     |
+-----------+-----------+              +-----------+-----------+
            |                                      |
            v                                      v
+-----------+-----------+              +-----------+-----------+
| ESP8266 + RC522 Node  |              | Teacher Portal (Web)  |
| (Campus Gate Reader)  |              |  Next.js 15 Frontend  |
+-----------+-----------+              +-----------+-----------+
            |                                      |
            | HTTP POST /api/kiosk/scan            | HTTP POST /api/lectures/{id}/photo
            | (Wi-Fi 802.11 b/g/n)                 | (REST API + JWT Bearer)
            v                                      v
+--------------------------------------------------------------+
|                     FastAPI Backend2 Core                    |
|                                                              |
|   +-------------------+              +-------------------+   |
|   | RFID Service      |              | AI Vision Engine  |   |
|   | - Debounce Filter |              | - SCRFD-10G ONNX  |   |
|   | - Idempotent Check|              | - 5-Pt Alignment  |   |
|   +---------+---------+              | - ArcFace 512-D   |   |
|             |                        +---------+---------+   |
|             |                                  |             |
|             +-----------------+----------------+             |
|                               |                              |
|                               v                              |
|               +---------------+---------------+              |
|               |  Two-Layer Attendance Matrix  |              |
|               |  - RFID + AI Cross-Validation |              |
|               |  - Strict PENDING Rule        |              |
|               +---------------+---------------+              |
+-------------------------------|------------------------------+
                                |
                                v
                +---------------+---------------+
                |   Database & Object Storage   |
                |   - SQLite (Dev Fallback)     |
                |   - PostgreSQL (Production)   |
                |   - Immutable Audit Logs      |
                +-------------------------------+
```

---

## 6. Technology Stack

### Frontend Client
- **Framework**: Next.js 15.3.3 (App Router, React 19)
- **Language**: TypeScript 5.8
- **Styling**: Tailwind CSS 3.4
- **Icons**: Lucide React
- **Edge Route Protection**: Native Edge Runtime Middleware (`src/middleware.ts`)

### Backend API
- **Framework**: FastAPI 0.110+ (Asynchronous REST API)
- **Runtime**: Python 3.12+
- **Data Validation**: Pydantic v2
- **ORM / Persistence**: SQLAlchemy 2.0
- **Security**: Native Bcrypt 4.1+ (72-byte safe slicing) & PyJWT (HS256)

### AI Vision Inference
- **Face Detector**: InsightFace SCRFD-10G ONNX (`scrfd_10g_bnkps.onnx`, 16.14 MB)
- **Feature Embedder**: ArcFace MobileFaceNet 512-D L2-normalized feature representation
- **Inference Engine**: ONNX Runtime 1.20+ (Optimized for `CPUExecutionProvider`)
- **Computer Vision**: OpenCV (`opencv-python` 4.8+) & NumPy 1.26+

### Hardware Node
- **Microcontroller**: NodeMCU ESP8266 12E (Tensilica 32-bit L106 @ 80/160 MHz)
- **RFID Transceiver**: NXP MFRC522 (RC522) 13.56 MHz SPI
- **Libraries**: `MFRC522` by GithubCommunity & `ArduinoJson` v6/v7

---

## 7. Two-Layer Verification Workflow

### Step 1: Morning Campus Physical Check-in
1. Student taps RFID card against campus gate reader.
2. ESP8266 reads card UID and issues `POST /api/kiosk/scan`.
3. Backend identifies student, verifies active status, and logs a record in `daily_checkins`.
4. Subsequent scans on the same calendar day return `ALREADY_CHECKED_IN` without creating duplicate records.

### Step 2: Classroom Lecture Biometric Verification
1. Teacher starts lecture session via Teacher Portal.
2. Teacher captures and uploads high-resolution classroom photograph (`POST /api/lectures/{id}/photo`).
3. SCRFD-10G ONNX detects all faces and extracts 5-point facial keypoints.
4. Faces are affine-aligned to $112 \times 112$ crops and mapped to 512-D normalized embeddings.
5. Embeddings are matched against enrolled division students using cosine similarity ($\tau = 0.70$).
6. Detections are cross-referenced with morning RFID logs:
   - RFID + AI $\implies$ **`PRESENT`**
   - RFID Only $\implies$ **`FLAGGED`** (Student on campus but missing from lecture photo)
   - AI Only $\implies$ **`FLAGGED`** (Student present in photo but missed morning RFID gate tap)
   - Neither $\implies$ **`PENDING`** (Never marked absent automatically)

### Step 3: Teacher Review & Finalization Lock
1. Teacher inspects the review roster and visual annotated overlay.
2. Teacher resolves flagged cases or manually marks verified students.
3. Teacher confirms finalization (`POST /api/lectures/{id}/finalize`):
   - Confirmed absences become `ABSENT`.
   - Unreviewed students remain `PENDING`.
   - Session status transitions to `FINALIZED`.
   - Permanent immutable lock engaged (`400 Bad Request` on subsequent modifications).
   - Structured audit entry written to `attendance_audit_logs`.

---

## 8. Hardware Connections & Pinout

```text
  NodeMCU ESP8266 12E                   MFRC522 RC522 Reader
  +------------------+                    +------------------+
  |             3.3V +------------------->+ 3.3V (VCC)       |  <-- DO NOT USE 5V!
  |              GND +------------------->+ GND              |
  |         D0 (G16) +------------------->+ RST              |
  |         D8 (G15) +------------------->+ SDA (SS)         |
  |         D5 (G14) +------------------->+ SCK              |
  |         D7 (G13) +------------------->+ MOSI             |
  |         D6 (G12) +------------------->+ MISO             |
  +------------------+                    +------------------+
```

Optional Status Indicators:
- **Green LED**: Pin `D1` (GPIO5) via 220Ω resistor $\to$ GND (Valid check-in)
- **Blue LED**: Pin `D2` (GPIO4) via 220Ω resistor $\to$ GND (Card assignment mode)
- **Active Buzzer**: Pin `D3` (GPIO0) $\to$ GND (Audio feedback)

---

## 9. Installation & Local Setup

### Prerequisites
- Node.js 18.x or 20.x
- Python 3.11 or 3.12
- Git

### 1. Clone Repository
```bash
git clone https://github.com/Developbyravi/Attendance-system.git
cd Attendance-system
```

### 2. Backend Setup
```bash
# Navigate to backend2 directory
cd backend2

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed default administrator, faculty, and demo student
python scripts/seed_demo_data.py

# Start Backend2 on port 8002
uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```
*Backend is now running at `http://127.0.0.1:8002`. Interactive docs at `http://127.0.0.1:8002/docs`.*

### 3. Frontend Setup
```bash
# Return to project root
cd ..

# Install Node dependencies
npm install

# Configure environment
cp .env.example .env.local

# Start Next.js development server
npm run dev
```
*Frontend web application is now running at `http://localhost:3000`.*

---

## 10. Default Demo Accounts

| Role | Username / Email | Password | Initial Dashboard |
| :--- | :--- | :--- | :--- |
| **Faculty (Teacher)** | `teacher@smartattend.edu` | `Teacher@123` | [`/teacher`](http://localhost:3000/teacher) |
| **Student (Ravi Khile)** | `khileravi207@gmail.com` *(or Roll: `10`)* | `Student@123` | [`/student`](http://localhost:3000/student) |
| **Institutional Admin** | `admin@smartattend.edu` | `Admin@123` | [`/admin`](http://localhost:3000/admin) |
| **Public Kiosk** | *Open Access* | *None* | [`/kiosk`](http://localhost:3000/kiosk) |

---

## 11. Core REST API Reference

### Daily RFID Morning Scan
```http
POST /api/attendance/rfid HTTP/1.1
Host: localhost:8002
Content-Type: application/json

{
  "rfid_uid": "4847B047",
  "device_id": "GATE-READER-01"
}
```

#### Response (`200 OK` — Verified Presence)
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
  "check_in_time": "2026-11-03T07:48:57.123Z",
  "date": "2026-11-03"
}
```

*For complete endpoint documentation across Auth, Lectures, Classes, and Devices, refer to [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md).*

---

## 12. Automated Testing Proof

The test suite runs 24 automated integration and biometrics tests without mocks:

```bash
# Run Pytest suite
pytest backend2/tests -v
```

```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: backend2, configfile: pytest.ini
collected 24 items

backend2/tests/api/test_endpoints.py::test_health_check_endpoint PASSED  [  4%]
backend2/tests/api/test_endpoints.py::test_classes_crud PASSED           [  8%]
backend2/tests/api/test_endpoints.py::test_student_and_teacher_crud PASSED [ 12%]
backend2/tests/api/test_endpoints.py::test_rfid_interactive_assignment_session PASSED [ 16%]
backend2/tests/api/test_endpoints.py::test_classroom_photo_verification_flow PASSED [ 20%]
backend2/tests/test_attendance.py::test_lecture_lifecycle_and_immutability PASSED [ 25%]
backend2/tests/test_attendance.py::test_teacher_lecture_isolation PASSED [ 29%]
backend2/tests/test_attendance.py::test_attendance_audit_log_persisted PASSED [ 33%]
backend2/tests/test_auth.py::test_login_and_token_generation PASSED      [ 37%]
backend2/tests/test_auth.py::test_login_invalid_password PASSED          [ 41%]
backend2/tests/test_auth.py::test_auth_me_endpoint PASSED                [ 45%]
backend2/tests/test_auth.py::test_role_enforcement_admin_only PASSED     [ 50%]
backend2/tests/test_auth.py::test_unauthorized_teacher_registration_rejected PASSED [ 54%]
backend2/tests/test_auth.py::test_public_student_registration_allowed PASSED [ 58%]
backend2/tests/test_auth.py::test_invalid_and_expired_tokens PASSED      [ 62%]
backend2/tests/test_database.py::test_database_tables_initialization PASSED [ 66%]
backend2/tests/test_face_detection.py::test_scrfd_detector_initialization PASSED [ 70%]
backend2/tests/test_face_detection.py::test_letterbox_aspect_ratio_preservation PASSED [ 75%]
backend2/tests/test_face_detection.py::test_crop_and_align_face PASSED   [ 79%]
backend2/tests/test_face_recognition.py::test_arcface_embedding_normalization PASSED [ 83%]
backend2/tests/test_face_recognition.py::test_cosine_similarity PASSED   [ 87%]
backend2/tests/test_face_recognition.py::test_matching_engine_disambiguation_and_same_person PASSED [ 91%]
backend2/tests/test_face_recognition.py::test_matching_engine_distinct_person_ambiguity PASSED [ 95%]
backend2/tests/test_rfid.py::test_daily_rfid_checkin_flow PASSED         [100%]

============================= 24 passed in 13.46s =============================
```

---

## 13. Security & Data Protection

- **Passwords**: Hashed with native `bcrypt` 4.1+ (72-byte safe string slicing).
- **Session Tokens**: PyJWT HS256 with 24-hour expiration and strict role claim verification.
- **Biometric Privacy**: No raw facial photos are committed to Git or exposed over unsecured endpoints. Facial profiles exist solely as 512-D non-invertible numerical embeddings.
- **Data Isolation**: Students cannot query other students' statistics (`403 Forbidden`). Faculty can only view and finalize lectures assigned to them.
- **Session Immutability**: Finalized lecture attendance cannot be edited without administrator overrides, with all changes logged in `attendance_audit_logs`.

---

## 14. Project Directory Structure

```text
Attendance-system/
├── src/                          # Next.js 15 Frontend Source
│   ├── app/                      # App Router Pages (/teacher, /student, /admin)
│   ├── components/               # Modular UI Components & Camera Capture
│   ├── context/                  # AuthContext Provider
│   ├── lib/                      # Central API Client & Typed Services
│   ├── types/                    # TypeScript Domain Interfaces
│   └── middleware.ts             # Edge Authentication & Role Boundary Guard
├── public/                       # Static Assets (favicon, icons)
├── backend2/                     # Active Production FastAPI Backend
│   ├── app/                      # Routers, Services, Models, Schemas, AI
│   ├── weights/                  # InsightFace SCRFD-10G ONNX (16.14 MB)
│   ├── tests/                    # 24 Pytest Automated Tests
│   ├── scripts/                  # Data Seeding & Live Verification Suites
│   ├── requirements.txt          # Python Dependencies
│   └── pytest.ini                # Pytest Configuration
├── firmware/                     # IoT Microcontroller Firmware
│   ├── esp8266_rfid_reader.ino   # ESP8266 + RC522 Production Sketch
│   └── README.md                 # Hardware Wiring & Setup Guide
├── deployment/                   # Cloud & Container Configuration
│   ├── Dockerfile                # Multi-stage Production Container
│   ├── docker-compose.yml        # Docker Composition (FastAPI + Postgres + Nginx)
│   ├── nginx.conf                # Nginx Reverse Proxy with Rate Limiting
│   ├── deploy.sh                 # Automated AWS EC2 Deployment Script
│   ├── AWS_EC2_SETUP.md          # EC2 t8i.small / Free Tier Setup Guide
│   ├── VERCEL_DEPLOYMENT.md      # Vercel Next.js Deployment Guide
│   ├── DATABASE_MIGRATION.md     # SQLite to PostgreSQL Migration Guide
│   ├── ENVIRONMENT_VARIABLES.md  # Detailed Environment Variables Catalog
│   ├── SECURITY_CHECKLIST.md     # Production Security Hardening Checklist
│   └── ROLLBACK_GUIDE.md         # Emergency Rollback Procedures
├── docs/                         # Detailed Architecture & Technical Reports
│   ├── ARCHITECTURE.md           # End-to-End Architectural Specification
│   ├── API_DOCUMENTATION.md      # Complete REST API Specification
│   ├── DATABASE_SCHEMA.md        # Database Models & ER Diagrams
│   ├── HARDWARE_SETUP.md         # Hardware Bill of Materials & Pinouts
│   └── PROJECT_REPORT.md         # Comprehensive Audit & Test Report
├── .gitignore                    # Professional Multi-Stack Git Exclusion
├── .env.example                  # Sanitized Global Environment Template
└── README.md                     # Master Technical Documentation
```

---

## 15. Contributor

- **Ravi Khile** ([@Developbyravi](https://github.com/Developbyravi)) — Lead Architect & Developer

---

## 16. License

This project is licensed under the [MIT License](LICENSE).
