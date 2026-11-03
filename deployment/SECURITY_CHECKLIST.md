# SmartAttend — Production Security & Hardening Checklist

## 1. Secrets Management
- [x] All `.env` files and `.env.local` excluded from version control via `.gitignore`.
- [x] `.env.example` provided with sanitized placeholders.
- [x] No `SUPABASE_SERVICE_ROLE_KEY` or database passwords committed to Git.
- [x] JWT `SECRET_KEY` randomly generated using `openssl rand -hex 32`.

## 2. Authentication & Authorization Boundaries
- [x] Passwords hashed with native `bcrypt` 4.1+ (72-byte safe slicing).
- [x] Public registration strictly restricted to students; teacher and admin account creation requires Admin Bearer token.
- [x] Student data isolation enforced: Students cannot view other students' statistics (`403 Forbidden`).
- [x] Teacher data isolation enforced: Teachers can only view, review, and finalize lecture sessions assigned to them (`403 Forbidden`).
- [x] Edge middleware route guards protecting `/admin`, `/teacher`, and `/student`.

## 3. Biometric & Student Privacy
- [x] No raw biometric face photos committed to repository.
- [x] Facial embeddings stored as mathematical 512-D vectors, non-invertible to original face photographs.
- [x] Upload directories (`/uploads/classroom/`, `/uploads/students/`) restricted and served through protected endpoints in production.

## 4. Network & Infrastructure
- [x] EC2 SSH port 22 restricted to authorized admin IP address.
- [x] Nginx reverse proxy with rate limiting (`30r/s` with burst of 50).
- [x] CORS origins explicitly whitelisted (`CORS_ORIGINS`).
- [x] HTTPS forced in production using Let's Encrypt SSL/TLS certificates.

## 5. Audit & Compliance
- [x] Attendance overrides and finalizations recorded in `attendance_audit_logs`.
- [x] Finalized lecture sessions locked permanently against tampering (`400 Bad Request`).
