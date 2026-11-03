/**
 * AIoT SmartAttend Authentication Types & Role Routing
 */

export type UserRole = "admin" | "teacher" | "student" | "parent";

export const ROLE_DISPLAY: Record<string, string> = {
  admin:   "Administrator",
  ADMIN:   "Administrator",
  teacher: "Teacher",
  TEACHER: "Teacher",
  student: "Student",
  STUDENT: "Student",
  parent:  "Parent",
  PARENT:  "Parent",
};

export const ROLE_HOME: Record<string, string> = {
  admin:   "/admin",
  ADMIN:   "/admin",
  teacher: "/teacher",
  TEACHER: "/teacher",
  student: "/student",
  STUDENT: "/student",
  parent:  "/parent",
  PARENT:  "/parent",
};

export interface AuthTokenResponse {
  access_token: string;
  token_type:   "bearer";
}

export interface AuthUser {
  id:         number | string;
  username:   string;
  email:      string;
  full_name:  string;
  role:       UserRole;
  is_active:  boolean;
  student_id?: string;
  class_name?: string;
  division?:   string;
}

export interface RegisterPayload {
  role: UserRole;
  name: string;
  email?: string;
  password: string;
  teacher_id?: string;
  department?: string;
  roll_no?: string;
  year?: string;
  division?: string;
  phone?: string;
}

export interface AuthContextValue {
  user:            AuthUser | null;
  token:           string | null;
  isLoading:       boolean;
  isAuthenticated: boolean;
  login:           (username: string, password: string, requestedRole?: UserRole) => Promise<void>;
  register:        (payload: RegisterPayload) => Promise<void>;
  logout:          () => Promise<void> | void;
  resetPassword?:  (email: string) => Promise<void>;
}
