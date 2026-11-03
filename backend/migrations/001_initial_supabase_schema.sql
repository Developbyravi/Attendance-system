-- =============================================================================
-- AIoT SmartAttend — Supabase PostgreSQL Production Schema & Migrations
-- Version: 1.0.0
-- Architecture: Role-Based Access Control, Real-Time Hardware Check-ins,
--               YOLO Face Detection & Multi-Factor Attendance Reconciliation
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. DIVISIONS & CLASSES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.divisions (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    department VARCHAR(100) NOT NULL,
    academic_year VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_division_dept_year UNIQUE (name, department, academic_year)
);

-- =============================================================================
-- 2. TEACHERS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.teachers (
    id BIGSERIAL PRIMARY KEY,
    teacher_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    department VARCHAR(100) NOT NULL DEFAULT 'Computer Science',
    is_active BOOLEAN DEFAULT TRUE,
    auth_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teachers_email ON public.teachers(email);
CREATE INDEX IF NOT EXISTS idx_teachers_auth_uid ON public.teachers(auth_user_id);

-- =============================================================================
-- 3. STUDENTS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.students (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    roll_no VARCHAR(50) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    year VARCHAR(50) NOT NULL,
    division VARCHAR(50) DEFAULT 'A',
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    rfid_uid VARCHAR(50) NOT NULL UNIQUE,
    face_enrolled BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    auth_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_students_roll_no ON public.students(roll_no);
CREATE INDEX IF NOT EXISTS idx_students_rfid_uid ON public.students(rfid_uid);
CREATE INDEX IF NOT EXISTS idx_students_division ON public.students(division);
CREATE INDEX IF NOT EXISTS idx_students_auth_uid ON public.students(auth_user_id);

-- =============================================================================
-- 4. PARENTS & GUARDIANS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.parents (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    auth_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_parents_phone ON public.parents(phone);
CREATE INDEX IF NOT EXISTS idx_parents_auth_uid ON public.parents(auth_user_id);

-- Parent-Student Link Table
CREATE TABLE IF NOT EXISTS public.parent_students (
    id BIGSERIAL PRIMARY KEY,
    parent_id BIGINT NOT NULL REFERENCES public.parents(id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) DEFAULT 'GUARDIAN',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_parent_student UNIQUE(parent_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_parent_students_parent ON public.parent_students(parent_id);
CREATE INDEX IF NOT EXISTS idx_parent_students_student ON public.parent_students(student_id);

-- =============================================================================
-- 5. FACE EMBEDDINGS (512-d Deep Feature Vectors)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.face_embeddings (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    embedding TEXT NOT NULL, -- JSON serialized 512-float vector
    image_reference VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_face_embeddings_student ON public.face_embeddings(student_id);

-- =============================================================================
-- 6. DAILY RFID CHECK-INS TABLE (Hardware Entry Gate Ingress)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.daily_checkins (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    rfid_uid VARCHAR(50) NOT NULL,
    first_scan_time TIMESTAMPTZ DEFAULT NOW(),
    last_scan_time TIMESTAMPTZ DEFAULT NOW(),
    scan_count INTEGER DEFAULT 1,
    device_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_daily_checkin_student_date UNIQUE(student_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_checkins_date ON public.daily_checkins(date);
CREATE INDEX IF NOT EXISTS idx_daily_checkins_student ON public.daily_checkins(student_id);

-- =============================================================================
-- 7. LECTURE SESSIONS TABLE (Timetabled Course Hours)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.lecture_sessions (
    id BIGSERIAL PRIMARY KEY,
    teacher_id BIGINT NOT NULL REFERENCES public.teachers(id),
    subject VARCHAR(100) NOT NULL,
    division VARCHAR(50) NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    start_time TIMESTAMPTZ DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE' 
        CHECK (status IN ('ACTIVE', 'VERIFYING', 'FINALIZED', 'CANCELLED')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lecture_sessions_teacher ON public.lecture_sessions(teacher_id);
CREATE INDEX IF NOT EXISTS idx_lecture_sessions_date ON public.lecture_sessions(date);
CREATE INDEX IF NOT EXISTS idx_lecture_sessions_division ON public.lecture_sessions(division);

-- =============================================================================
-- 8. LECTURE ATTENDANCES TABLE (Reconciled Attendance Ledger)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.lecture_attendances (
    id BIGSERIAL PRIMARY KEY,
    lecture_session_id BIGINT NOT NULL REFERENCES public.lecture_sessions(id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL 
        CHECK (status IN ('PRESENT', 'ABSENT', 'FLAGGED')),
    verification_source VARCHAR(50) NOT NULL 
        CHECK (verification_source IN ('RFID_AND_AI', 'RFID_ONLY', 'AI_ONLY', 'TEACHER_CONFIRMED', 'TEACHER_MARKED_ABSENT', 'ABSENT')),
    ai_confidence DOUBLE PRECISION,
    rfid_checked_in BOOLEAN DEFAULT FALSE,
    ai_detected BOOLEAN DEFAULT FALSE,
    teacher_action VARCHAR(50),
    finalized BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_lecture_attendance_session_student UNIQUE(lecture_session_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_lecture_att_session ON public.lecture_attendances(lecture_session_id);
CREATE INDEX IF NOT EXISTS idx_lecture_att_student ON public.lecture_attendances(student_id);
CREATE INDEX IF NOT EXISTS idx_lecture_att_status ON public.lecture_attendances(status);

-- =============================================================================
-- 9. AUDIT LOGS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(50) NOT NULL,
    details TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON public.audit_logs(entity_type, entity_id);

-- =============================================================================
-- 10. ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================
ALTER TABLE public.students ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.teachers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.parents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.parent_students ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_checkins ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lecture_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lecture_attendances ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Helper function: Is Admin?
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN (auth.jwt() ->> 'role' = 'admin' OR auth.jwt() -> 'app_metadata' ->> 'role' = 'admin');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- STUDENTS POLICIES
CREATE POLICY "Admins have full access to students" 
    ON public.students FOR ALL 
    USING (public.is_admin());

CREATE POLICY "Teachers can view students in their department" 
    ON public.students FOR SELECT 
    USING (auth.jwt() ->> 'role' = 'teacher' OR EXISTS (SELECT 1 FROM public.teachers WHERE auth_user_id = auth.uid()));

CREATE POLICY "Students can view their own profile" 
    ON public.students FOR SELECT 
    USING (auth_user_id = auth.uid());

CREATE POLICY "Parents can view linked students" 
    ON public.students FOR SELECT 
    USING (EXISTS (
        SELECT 1 FROM public.parent_students ps
        JOIN public.parents p ON ps.parent_id = p.id
        WHERE ps.student_id = public.students.id AND p.auth_user_id = auth.uid()
    ));

-- DAILY CHECK-INS POLICIES
CREATE POLICY "Admins can view and manage all daily checkins" 
    ON public.daily_checkins FOR ALL 
    USING (public.is_admin());

CREATE POLICY "Teachers can view daily checkins" 
    ON public.daily_checkins FOR SELECT 
    USING (auth.jwt() ->> 'role' = 'teacher' OR EXISTS (SELECT 1 FROM public.teachers WHERE auth_user_id = auth.uid()));

CREATE POLICY "Students can view their own checkins" 
    ON public.daily_checkins FOR SELECT 
    USING (EXISTS (SELECT 1 FROM public.students s WHERE s.id = daily_checkins.student_id AND s.auth_user_id = auth.uid()));

CREATE POLICY "Parents can view linked children checkins" 
    ON public.daily_checkins FOR SELECT 
    USING (EXISTS (
        SELECT 1 FROM public.parent_students ps
        JOIN public.parents p ON ps.parent_id = p.id
        WHERE ps.student_id = daily_checkins.student_id AND p.auth_user_id = auth.uid()
    ));

-- LECTURE SESSIONS POLICIES
CREATE POLICY "Admins have full access to lecture sessions" 
    ON public.lecture_sessions FOR ALL 
    USING (public.is_admin());

CREATE POLICY "Teachers can manage their own lectures" 
    ON public.lecture_sessions FOR ALL 
    USING (EXISTS (SELECT 1 FROM public.teachers t WHERE t.id = lecture_sessions.teacher_id AND t.auth_user_id = auth.uid()));

CREATE POLICY "Students can view lectures for their division" 
    ON public.lecture_sessions FOR SELECT 
    USING (EXISTS (SELECT 1 FROM public.students s WHERE s.division = lecture_sessions.division AND s.auth_user_id = auth.uid()));

-- LECTURE ATTENDANCES POLICIES
CREATE POLICY "Admins have full access to attendances" 
    ON public.lecture_attendances FOR ALL 
    USING (public.is_admin());

CREATE POLICY "Teachers can view and review attendances for their lectures" 
    ON public.lecture_attendances FOR ALL 
    USING (EXISTS (
        SELECT 1 FROM public.lecture_sessions ls
        JOIN public.teachers t ON ls.teacher_id = t.id
        WHERE ls.id = lecture_attendances.lecture_session_id AND t.auth_user_id = auth.uid()
    ));

CREATE POLICY "Students can view only their own attendances" 
    ON public.lecture_attendances FOR SELECT 
    USING (EXISTS (SELECT 1 FROM public.students s WHERE s.id = lecture_attendances.student_id AND s.auth_user_id = auth.uid()));

CREATE POLICY "Parents can view linked children attendances" 
    ON public.lecture_attendances FOR SELECT 
    USING (EXISTS (
        SELECT 1 FROM public.parent_students ps
        JOIN public.parents p ON ps.parent_id = p.id
        WHERE ps.student_id = lecture_attendances.student_id AND p.auth_user_id = auth.uid()
    ));

-- =============================================================================
-- 11. STORAGE BUCKET CONFIGURATION & POLICIES
-- =============================================================================
-- Insert storage buckets if not present
INSERT INTO storage.buckets (id, name, public) 
VALUES 
    ('classroom-images', 'classroom-images', false),
    ('student-enrollments', 'student-enrollments', false)
ON CONFLICT (id) DO NOTHING;

-- Storage policies: Authorized faculty can upload classroom images
CREATE POLICY "Faculty classroom image upload" 
    ON storage.objects FOR INSERT 
    WITH CHECK (bucket_id = 'classroom-images' AND (auth.role() = 'authenticated'));

CREATE POLICY "Authorized classroom image read" 
    ON storage.objects FOR SELECT 
    USING (bucket_id = 'classroom-images' AND (auth.role() = 'authenticated'));

-- Storage policies: Admin / service-role can manage student enrollments
CREATE POLICY "Student enrollment images read" 
    ON storage.objects FOR SELECT 
    USING (bucket_id = 'student-enrollments' AND (auth.role() = 'authenticated'));
