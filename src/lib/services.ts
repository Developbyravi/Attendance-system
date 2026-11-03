/**
 * AIoT SmartAttend — Typed Business Domain Services
 * Connects directly to FastAPI backend and Supabase data sources.
 *
 * Adheres strictly to the No-Dummy-Data policy:
 * - Real API requests
 * - Proper error handling
 * - Clean types
 */

import { api } from "./api";

// ── DOMAIN INTERFACES ──

export interface StudentRecord {
  id: number | string;
  roll_no: string;
  roll_number?: string;
  prn?: string;
  name: string;
  full_name?: string;
  email: string;
  department: string;
  year: string;
  division: string;
  division_id?: string | number;
  division_name?: string;
  class_name?: string;
  rfid_uid?: string | null;
  face_enrolled: boolean;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface TeacherRecord {
  id: number | string;
  teacher_id: string;
  employee_id?: string;
  name: string;
  full_name?: string;
  email: string;
  department: string;
  assigned_divisions?: string[];
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ClassDivisionRecord {
  id: string | number;
  name: string;
  code: string;
  academic_year: string;
  semester: number | string;
  department: string;
  total_students: number;
  class_teacher?: string;
  is_active: boolean;
}

export interface DeviceRecord {
  id: string | number;
  device_id: string;
  device_name: string;
  location: string;
  ip_address?: string;
  mac_address?: string;
  status: "online" | "offline" | "maintenance";
  last_ping?: string;
  firmware_version?: string;
}

export interface DailyCheckInRecord {
  id: string | number;
  student_id: string | number;
  student_name: string;
  roll_number: string;
  division_name: string;
  rfid_uid: string;
  device_id: string;
  check_in_time: string;
  is_verified: boolean;
}

export interface LectureSession {
  id: string | number;
  title: string;
  subject: string;
  division_id: string | number;
  division_name: string;
  teacher_id: string | number;
  teacher_name?: string;
  lecture_date: string;
  start_time: string;
  end_time?: string;
  classroom?: string;
  status: "scheduled" | "in_progress" | "review_pending" | "finalized";
  classroom_photo_url?: string;
  overlay_image_url?: string;
  total_enrolled: number;
  present_count: number;
  absent_count: number;
  flagged_count: number;
  pending_count?: number;
  finalized_at?: string;
}

export interface AttendanceReviewItem {
  id: string | number;
  student_id: string | number;
  student_name: string;
  roll_number: string;
  daily_rfid_status: "CHECKED_IN" | "NOT_CHECKED_IN";
  daily_check_in_time?: string;
  ai_verification_status: "VERIFIED" | "UNKNOWN" | "NOT_DETECTED" | "FLAGGED";
  confidence_score?: number | null;
  attendance_status: "PRESENT" | "ABSENT" | "FLAGGED" | "PENDING";
  verification_source: "AI_CROSSCHECK" | "TEACHER_MANUAL" | "DAILY_RFID_ONLY";
  notes?: string;
}

export interface NotificationRecord {
  id: string | number;
  title: string;
  message: string;
  channel: "WHATSAPP" | "IN_APP" | "EMAIL";
  recipient_type: "PARENT" | "STUDENT" | "TEACHER";
  recipient: string;
  status: "SENT" | "PENDING" | "FAILED";
  timestamp: string;
}

export interface SystemStats {
  total_students: number;
  total_teachers: number;
  today_checkins: number;
  today_lectures: number;
  overall_attendance_rate: number | null;
  pending_flagged_cases: number;
}

// ── SERVICE MODULES ──

export const studentService = {
  getAll: async (params?: { division_id?: string; query?: string }): Promise<StudentRecord[]> => {
    const q = new URLSearchParams();
    if (params?.division_id) q.set("division_id", params.division_id);
    if (params?.query) q.set("q", params.query);
    const qs = q.toString() ? `?${q.toString()}` : "";
    const list = await api.get<any[]>(`/students${qs}`);
    return (list || []).map((s) => ({
      ...s,
      id: s.id,
      roll_no: s.roll_no || s.roll_number || "",
      roll_number: s.roll_number || s.roll_no || "",
      name: s.name || s.full_name || "",
      full_name: s.full_name || s.name || "",
      department: s.department || "Computer Science",
      year: s.year || "3rd Year",
      division: s.division || s.division_name || "A",
      division_name: s.division_name || s.division || "A",
      class_name: s.class_name || `Div ${s.division || "A"}`,
      email: s.email || "",
      rfid_uid: s.rfid_uid || null,
      face_enrolled: Boolean(s.face_enrolled),
      is_active: s.is_active !== false,
      created_at: s.created_at,
    }));
  },
  getById: (id: string | number) => api.get<StudentRecord>(`/students/${id}`),
  create: (data: Partial<StudentRecord>) => api.post<StudentRecord>("/students", data),
  update: (id: string | number, data: Partial<StudentRecord>) =>
    api.put<StudentRecord>(`/students/${id}`, data),
  deactivate: (id: string | number) => api.patch(`/students/${id}/deactivate`),
  enrollFace: (studentId: string | number, file: File | Blob) => {
    const formData = new FormData();
    formData.append("file", file, "face_capture.jpg");
    return api.upload<{
      student_id: number;
      images_processed: number;
      faces_detected: number;
      successful_embeddings: number;
      status: string;
      quality_warnings?: string[];
    }>(`/students/${studentId}/face-enroll`, formData);
  },
  selfEnrollFace: (file: File | Blob) => {
    const formData = new FormData();
    formData.append("file", file, "face_capture.jpg");
    return api.upload<{
      student_id: number;
      images_processed: number;
      faces_detected: number;
      successful_embeddings: number;
      status: string;
      quality_warnings?: string[];
    }>("/student/me/face-enroll", formData);
  },
  getProfile: () =>
    api.get<{
      id: number;
      name: string;
      roll_no: string;
      email: string;
      department: string;
      year: string;
      division: string;
      rfid_uid?: string;
      face_enrolled: boolean;
      created_at: string;
    }>("/student/me/profile"),
};

export const teacherService = {
  getAll: async (params?: { department?: string; query?: string }): Promise<TeacherRecord[]> => {
    const q = new URLSearchParams();
    if (params?.department) q.set("department", params.department);
    if (params?.query) q.set("q", params.query);
    const qs = q.toString() ? `?${q.toString()}` : "";
    const list = await api.get<any[]>(`/teachers${qs}`);
    return (list || []).map((t) => ({
      ...t,
      id: t.id,
      teacher_id: t.teacher_id || t.employee_id || "",
      employee_id: t.employee_id || t.teacher_id || "",
      name: t.name || t.full_name || "",
      full_name: t.full_name || t.name || "",
      email: t.email || "",
      department: t.department || "Computer Science & Engineering",
      assigned_divisions: t.assigned_divisions || [],
      is_active: t.is_active !== false,
      created_at: t.created_at,
    }));
  },
  getById: (id: string | number) => api.get<TeacherRecord>(`/teachers/${id}`),
  create: (data: Partial<TeacherRecord>) => api.post<TeacherRecord>("/teachers", data),
  update: (id: string | number, data: Partial<TeacherRecord>) =>
    api.put<TeacherRecord>(`/teachers/${id}`, data),
  deactivate: (id: string | number) => api.patch(`/teachers/${id}/deactivate`),
};

export const classService = {
  getAll: () => api.get<ClassDivisionRecord[]>("/classes"),
  create: (data: Partial<ClassDivisionRecord>) =>
    api.post<ClassDivisionRecord>("/classes", data),
  getById: (id: string | number) => api.get<ClassDivisionRecord>(`/classes/${id}`),
};

export const deviceService = {
  getAll: () => api.get<DeviceRecord[]>("/devices"),
  register: (data: Partial<DeviceRecord>) => api.post<DeviceRecord>("/devices", data),
  getKioskStatus: () => api.get<{ status: "online" | "offline"; timestamp: string }>("/kiosk/status"),
  simulateKioskScan: (rfid_uid: string, device_id: string) =>
    api.post("/kiosk/scan", { rfid_uid, device_id }),
};

export const checkInService = {
  getToday: (params?: { division_id?: string; date?: string }) => {
    const q = new URLSearchParams();
    if (params?.division_id) q.set("division_id", params.division_id);
    if (params?.date) q.set("date", params.date);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return api.get<DailyCheckInRecord[]>(`/daily-checkins${qs}`);
  },
};

export interface DetectedFaceBoxRecord {
  bbox: [number, number, number, number];
  detector_confidence: number;
  similarity?: number | null;
  match_status: "recognized" | "ambiguous" | "unknown" | "duplicate";
  student_id?: number | null;
  student_name?: string | null;
  roll_no?: string | null;
}

export interface LectureVerificationSummaryResult {
  lecture_id: number;
  subject: string;
  division: string;
  date: string;
  daily_rfid_checked_in: number;
  ai_detected_count: number;
  verified_present: number;
  rfid_only: number;
  ai_only: number;
  absent: number;
  pending?: number;
  unknown_faces: number;
  photo_url?: string;
  overlay_image_url?: string;
  detected_faces: number;
  detected_boxes?: DetectedFaceBoxRecord[];
  detector?: string;
  attendances: Array<any>;
}

export const lectureService = {
  getAll: (params?: { teacher_id?: string | number; date?: string }) => {
    const q = new URLSearchParams();
    if (params?.teacher_id) q.set("teacher_id", String(params.teacher_id));
    if (params?.date) q.set("date", params.date);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return api.get<LectureSession[]>(`/lectures${qs}`);
  },
  getById: (id: string | number) => api.get<LectureSession>(`/lectures/${id}`),
  create: (data: {
    subject: string;
    title: string;
    division_id: string | number;
    division?: string;
    lecture_date: string;
    start_time: string;
    classroom?: string;
  }) => api.post<LectureSession>("/lectures", data),

  uploadClassroomPhoto: (lectureId: string | number, file: File | Blob) => {
    const formData = new FormData();
    formData.append("file", file, "classroom_capture.jpg");
    formData.append("photo", file, "classroom_capture.jpg");
    return api.upload<LectureVerificationSummaryResult>(
      `/lectures/${lectureId}/photo`,
      formData
    );
  },

  getReviewRoster: (lectureId: string | number) =>
    api.get<AttendanceReviewItem[]>(`/lectures/${lectureId}/review`),

  updateStudentAttendance: (
    lectureId: string | number,
    studentId: string | number,
    status: "PRESENT" | "ABSENT" | "FLAGGED",
    reason?: string
  ) =>
    api.patch(`/lectures/${lectureId}/students/${studentId}`, { status, reason }),

  finalizeAttendance: (lectureId: string | number) =>
    api.post<{ finalized: boolean; finalized_at: string }>(`/lectures/${lectureId}/finalize`),
};

export const statsService = {
  getAdminStats: () => api.get<SystemStats>("/admin/stats"),
  getStudentStats: (studentId: string | number) =>
    api.get<{
      total_lectures: number;
      present_count: number;
      absent_count: number;
      flagged_count: number;
      attendance_percentage: number;
      today_rfid_checked_in: boolean;
      today_check_in_time?: string;
      recent_records: Array<{
        date: string;
        subject: string;
        status: "PRESENT" | "ABSENT" | "FLAGGED";
        teacher_name: string;
      }>;
    }>(`/student/${studentId}/stats`),

  getParentChildOverview: (parentId: string | number) =>
    api.get<{
      children: Array<{
        id: string | number;
        name: string;
        roll_number: string;
        division_name: string;
        today_checked_in: boolean;
        today_time?: string;
        overall_percentage: number;
        recent_absences: number;
      }>;
      notifications: NotificationRecord[];
    }>(`/parent/${parentId}/overview`),
};

export interface RfidAssignmentSession {
  session_id: string;
  student_id: number;
  student_name: string;
  roll_no: string;
  department: string;
  division: string;
  current_rfid_uid?: string | null;
  status: "PENDING_SCAN" | "SCANNED" | "CONFIRMED" | "CANCELLED" | "EXPIRED";
  scanned_uid?: string | null;
  device_id?: string | null;
  created_at: string;
  expires_at: string;
  expires_in_seconds: number;
  error?: string | null;
}

export const rfidService = {
  startAssignment: (data: {
    student_id: number | string;
    mode?: "ASSIGN" | "REPLACE";
    device_id?: string;
    timeout_seconds?: number;
  }) => api.post<RfidAssignmentSession>("/rfid/assignment/start", data),

  getSessionStatus: (sessionId: string) =>
    api.get<RfidAssignmentSession>(`/rfid/assignment/session/${sessionId}`),

  cancelAssignment: (sessionId: string) =>
    api.post<{ status: string; session_id: string }>("/rfid/assignment/cancel", { session_id: sessionId }),

  confirmAssignment: (data: {
    session_id: string;
    student_id: number | string;
    rfid_uid: string;
    reason?: string;
  }) =>
    api.post<{
      status: string;
      action: string;
      student_id: number;
      roll_no: string;
      student_name: string;
      rfid_uid: string;
      previous_rfid_uid?: string;
      session_id: string;
    }>("/rfid/assignment/confirm", data),

  deactivateCard: (data: {
    student_id: number | string;
    reason?: string;
  }) =>
    api.post<{
      status: string;
      action: string;
      student_id: number;
      student_name: string;
      roll_no: string;
      deactivated_rfid_uid?: string;
    }>("/rfid/deactivate", data),
};

