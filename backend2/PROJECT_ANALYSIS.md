# SmartAttend AI-Based Attendance Management System
## Backend Re-Architecture & Project Analysis (Phase 1)

### 1. Existing Frontend Architecture
The frontend is a modern **Next.js 15** web application using:
- **TypeScript** with strict domain types (`StudentRecord`, `TeacherRecord`, `LectureSession`, `AttendanceReviewItem`, `RfidAssignmentSession`, etc.).
- **Tailwind CSS** for institutional dark UI theming.
- **Lucide React** for UI iconography.
- **React 19 Hooks** (`use(params)`, `useState`, `useEffect`).
- **Client-Side Auth Context (`AuthContext.tsx`)**: Manages JWT token persistence in `localStorage`, role routing (`/admin`, `/teacher`, `/student`, `/parent`), login, signup, and user sessions.
- **Unified API Client (`src/lib/api.ts`)**: Centralizes HTTP requests pointing to `NEXT_PUBLIC_API_URL` (defaulting to `http://localhost:8001/api` for backend, and configured to port `8002` for `backend2`). Handles Bearer token headers, JSON and multipart/form-data payloads, and structured `ApiError` propagation.
- **Business Domain Services (`src/lib/services.ts`)**: Modular service facade encapsulating:
  - `studentService`: CRUD, face enrollment (`POST /students/{id}/face-enroll`, `POST /student/me/face-enroll`), profile retrieval (`GET /student/me/profile`).
  - `teacherService`: CRUD, division assignments.
  - `classService`: Class & division definitions.
  - `deviceService`: RFID reader registration, kiosk health polling (`GET /kiosk/status`), scan simulation (`POST /kiosk/scan`).
  - `checkInService`: Daily RFID check-in ledger (`GET /daily-checkins`).
  - `lectureService`: Lecture lifecycle (`GET /lectures`, `POST /lectures`, `GET /lectures/{id}`, `POST /lectures/{id}/photo`, `GET /lectures/{id}/review`, `PATCH /lectures/{id}/students/{id}`, `POST /lectures/{id}/finalize`).
  - `rfidService`: Interactive hardware card assignment (`POST /rfid/assignment/start`, `GET /rfid/assignment/session/{id}`, `POST /rfid/assignment/confirm`, `POST /rfid/assignment/cancel`, `POST /rfid/deactivate`).
  - `statsService`: Admin overview stats (`GET /admin/stats`), student stats (`GET /student/{id}/stats`), parent-child monitoring (`GET /parent/{id}/overview`).

---

### 2. All Expected API Endpoints (Frontend Contract Matrix)

| Endpoint | Method | Role / Auth | Description |
|---|---|---|---|
| `/api/auth/token` | POST | Public | OAuth2 Password Request (`username`, `password`) -> `{ access_token, token_type }` |
| `/api/auth/register` | POST | Public / Admin | Unified user registration (`email`, `password`, `role`, `name`, details) |
| `/api/auth/me` | GET | Authenticated | Current user profile, role, and linked entity info |
| `/api/auth/link-profile` | POST | Authenticated | Post-Supabase signup linking |
| `/api/students` | GET | Teacher / Admin | List students filtered by `division_id`, `q` search query |
| `/api/students` | POST | Admin | Register new student record |
| `/api/students/{id}` | GET | Teacher / Admin | Student record details |
| `/api/students/{id}` | PUT | Admin | Update student record |
| `/api/students/{id}/deactivate`| PATCH | Admin | Soft-deactivate student account |
| `/api/students/{id}/face-enroll` | POST | Admin / Teacher | Upload face image for biometric enrollment (multipart) |
| `/api/student/me/profile` | GET | Student | Authenticated student's own institutional & biometric profile |
| `/api/student/me/face-enroll` | POST | Student | Student self-enrollment of facial biometrics (multipart) |
| `/api/student/{id}/stats` | GET | Student / Admin | Student attendance statistics, percentage, and recent history |
| `/api/teachers` | GET | Admin | List teachers filtered by department / query |
| `/api/teachers` | POST | Admin | Create teacher profile |
| `/api/teachers/{id}` | GET | Admin | Teacher details |
| `/api/teachers/{id}` | PUT | Admin | Update teacher record |
| `/api/teachers/{id}/deactivate`| PATCH | Admin | Soft-deactivate teacher |
| `/api/classes` | GET | Teacher / Admin | List all academic classes & divisions |
| `/api/classes` | POST | Admin | Create class/division record |
| `/api/classes/{id}` | GET | Teacher / Admin | Division details & student count |
| `/api/devices` | GET | Admin | List active IoT devices & RFID gateways |
| `/api/devices` | POST | Admin | Register IoT device |
| `/api/kiosk/status` | GET | Public / Kiosk | Hardware gateway health ping & status |
| `/api/kiosk/scan` | POST | Kiosk / IoT | Ingest RFID tap from reader |
| `/api/attendance/rfid` | POST | Public / IoT / Kiosk | Canonical Daily RFID check-in endpoint (`rfid_uid`) |
| `/api/daily-checkins` | GET | Teacher / Admin | Retrieve daily RFID check-in logs filtered by `division_id`, `date` |
| `/api/lectures` | GET | Teacher / Admin | List lectures filtered by `teacher_id`, `date` |
| `/api/lectures` | POST | Teacher | Schedule / start a lecture session |
| `/api/lectures/{id}` | GET | Teacher / Admin | Lecture details, status, photo URL, and attendance roster |
| `/api/lectures/{id}/photo` | POST | Teacher | Upload classroom image, detect faces (SCRFD), match embeddings (ArcFace), cross-verify with RFID |
| `/api/lectures/{id}/review` | GET | Teacher | Review roster with flagged items, candidate matches, and confidence |
| `/api/lectures/{id}/students/{student_id}` | PATCH | Teacher | Manually override student attendance (`status`, `reason`) |
| `/api/lectures/{id}/finalize` | POST | Teacher | Lock lecture attendance as immutable |
| `/api/rfid/assignment/start` | POST | Admin | Initiate 60s interactive card scan session on hardware reader |
| `/api/rfid/assignment/session/{id}` | GET | Admin | Poll card scan session status |
| `/api/rfid/assignment/confirm` | POST | Admin | Confirm card UID assignment to student |
| `/api/rfid/assignment/cancel` | POST | Admin | Abort card assignment session |
| `/api/rfid/deactivate` | POST | Admin | Revoke / clear student RFID card |
| `/api/admin/stats` | GET | Admin | Institutional high-level KPI stats |
| `/api/parent/{id}/overview` | GET | Parent | Enrolled children overview, attendance %, notifications |
| `/api/health` | GET | Public | Backend health, database, detector, model, and storage status |

---

### 3. Request and Response Formats
Standardized JSON envelop format across all API endpoints:
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```
Direct FastAPI schema responses (e.g., `LectureVerificationSummary`, `AttendanceReviewItem[]`, `StudentRecord[]`) will be supported seamlessly to maintain strict 1:1 compatibility with existing frontend TypeScript interfaces.

---

### 4. Database Requirements & Normalized Entities
1. **Users (`users`)**:
   - `id` (PK, int), `email` (unique), `hashed_password` (string), `role` (`ADMIN`, `TEACHER`, `STUDENT`, `PARENT`), `is_active` (bool), `auth_user_id` (UUID optional for Supabase sync), `created_at`, `updated_at`.
2. **Teachers (`teachers`)**:
   - `id` (PK), `user_id` (FK -> users.id), `teacher_id` (unique code), `name`, `email`, `department`, `assigned_divisions` (JSON array), `is_active`, `created_at`.
3. **Classes & Divisions (`classes`, `divisions`)**:
   - `id` (PK), `name` ("A", "B", etc.), `code`, `academic_year`, `semester`, `department`, `total_students`, `is_active`.
4. **Subjects (`subjects`)**:
   - `id` (PK), `name`, `code`, `department`, `semester`, `is_active`.
5. **Students (`students`)**:
   - `id` (PK), `user_id` (FK optional -> users.id), `roll_no` (unique per division), `name`, `email` (unique), `department`, `year`, `division_id` (FK -> divisions.id) / `division` string, `rfid_uid` (unique, nullable), `face_enrolled` (bool), `is_active` (bool), `created_at`.
6. **Daily Check-ins (`daily_checkins`)**:
   - `id` (PK), `student_id` (FK -> students.id), `date` (Date, indexed), `check_in_time` (DateTime), `rfid_uid` (string), `device_id` (string), `is_verified` (bool). Unique constraint: `(student_id, date)`.
7. **Lecture Sessions (`lecture_sessions`)**:
   - `id` (PK), `teacher_id` (FK -> teachers.id), `subject_id` / `subject` (string), `division_id` / `division` (string), `date` (Date), `start_time` (Time), `end_time` (Time nullable), `status` (`SCHEDULED`, `IN_PROGRESS`, `REVIEW_PENDING`, `FINALIZED`), `classroom` (string), `classroom_photo_url` (string nullable), `overlay_image_url` (string nullable), `created_at`.
8. **Lecture Attendance (`lecture_attendances`)**:
   - `id` (PK), `lecture_session_id` (FK -> lecture_sessions.id), `student_id` (FK -> students.id), `status` (`PRESENT`, `FLAGGED`, `PENDING`, `ABSENT`), `verification_source` (`RFID_AND_AI`, `AI_ONLY`, `RFID_ONLY`, `TEACHER_CONFIRMED`, `TEACHER_MANUAL`, `FINALIZED_ABSENT`, `UNVERIFIED`), `ai_confidence` (float nullable), `rfid_checked_in` (bool), `ai_detected` (bool), `teacher_action` (string nullable), `finalized` (bool), `created_at`. Unique constraint: `(lecture_session_id, student_id)`.
9. **Face Embeddings (`face_embeddings`)**:
   - `id` (PK), `student_id` (FK -> students.id), `embedding` (JSON array of 512 floats), `image_reference` (string), `quality_score` (float), `created_at`.
10. **Attendance Audit Logs (`attendance_audit_logs`)**:
    - `id` (PK), `user_id` (string), `role` (string), `action` (string), `entity_type` (string), `entity_id` (string), `details` (JSON), `timestamp` (DateTime).

---

### 5. Authentication & Role-Based Authorization
- **JWT Provider**: HS256 JWT tokens with standard claims (`sub` = user_id, `role` = role, `email` = email, `exp` = expiration).
- **Password Security**: Argon2 or BCrypt with constant-time verification.
- **Roles**:
  - `ADMIN`: Full access to all endpoints, CRUD on students, teachers, classes, RFID assignment.
  - `TEACHER`: Access to assigned lectures, rosters, photo upload, flag resolution, finalization.
  - `STUDENT`: Read-only access to own profile (`/student/me/*`), attendance stats (`/student/{id}/stats`), self biometric enrollment.
  - `PARENT`: Read-only access to enrolled children's stats.
- **Supabase Fallback / Sync**: If Supabase JWT is passed in `Authorization: Bearer`, decode and verify against Supabase JWT secret or local secret seamlessly.

---

### 6. Daily RFID Check-In System
- Morning physical tap at campus gate/kiosk reader.
- Endpoint: `POST /api/attendance/rfid` with `{"rfid_uid": "..."}` (or `/api/kiosk/scan` with `{"rfid_uid": "...", "device_id": "..."}`).
- Verifies student exists and is active.
- Idempotent: If student already checked in for today's date, returns HTTP 200 with status `"ALREADY_CHECKED_IN"`.
- Otherwise records `DailyCheckinModel` with timestamp and returns HTTP 200 with student details and check-in confirmation.

---

### 7. AI Face Detection and Recognition Pipeline
- **Detector**: InsightFace SCRFD-10G (`scrfd_10g_bnkps.onnx`), 3-scale feature pyramid (strides 8, 16, 32), multi-face support down to small distant classroom faces, aspect-ratio-preserving letterboxing, 5-point facial landmarks.
- **Aligner**: 5-point landmark affine transformation aligning eyes, nose, and mouth corners to canonical 112x112 coordinates.
- **Embedder**: ArcFace-MobileFaceNet generating L2-normalized 512-dimensional float vectors ($||\vec{v}||_2 = 1.0$).
- **Matching Engine**: Cosine similarity against all enrolled division student embeddings:
  - If similarity $\ge 0.70$ and margin against second candidate $\ge 0.08$: `RECOGNIZED`.
  - If similarity $\ge 0.70$ and margin $< 0.08$ with different candidates: `AMBIGUOUS` (flagged for review; RFID used for automatic disambiguation if exactly one candidate checked in).
  - If candidate accounts share the identical person/name: automatically merged to prevent self-conflict.
  - If similarity $< 0.70$: `UNKNOWN`.
  - Duplicate face removal: Prevents multiple faces from matching the same student without explicit justification.

---

### 8. AI Attendance Cross-Verification Matrix
During a lecture:
1. Teacher uploads classroom image.
2. System detects all faces, extracts landmarks, generates embeddings, and identifies matching candidates strictly within the lecture's division.
3. System fetches today's RFID check-in status for division students.
4. Matrix cross-verification:
   - **PRESENT**: Both Daily RFID Check-in completed AND Face verified by AI.
   - **FLAGGED (AI_ONLY)**: Face detected in classroom, but student missed morning RFID check-in.
   - **FLAGGED (RFID_ONLY)**: Student tapped RFID in morning, but face not detected in this classroom image.
   - **FLAGGED (AMBIGUOUS_AI)**: Face detected with multiple close matches; surfaced to teacher with candidate chips for one-click confirmation.
   - **PENDING**: Student has no RFID and no face detection; remains pending during lecture so one image never prematurely marks students absent.
   - **FINALIZED_ABSENT**: When teacher reviews and finalizes lecture session (`POST /lectures/{id}/finalize`), all remaining pending records transition to `ABSENT` and are permanently locked as immutable.

---

### 9. Proposed Backend2 Architecture
- Completely isolated under `backend2/`.
- Runs on **port 8002** via `uvicorn app.main:app --host 127.0.0.1 --port 8002`.
- Uses SQLAlchemy 2.0 async/sync with clean repository pattern.
- Supports SQLite local development (`backend2/smartattend.db`) and PostgreSQL/Supabase production seamlessly.
- Full automated test suite in `backend2/tests/` covering unit, integration, API, and edge cases.
- Zero modification to legacy `backend/`.

