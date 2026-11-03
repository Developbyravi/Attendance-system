/**
 * SmartAttend — Centralized API Client
 *
 * All HTTP requests go through this module.
 * Base URL is read from NEXT_PUBLIC_API_URL — never hardcoded.
 *
 * Backend: FastAPI on http://localhost:8001/api
 *
 * Usage:
 *   import { api } from "@/lib/api";
 *   const user = await api.get<AuthUser>("/auth/me");
 *   await api.post("/lectures", { subject, division_id });
 */

import type { AuthTokenResponse, AuthUser, RegisterPayload } from "@/types/auth";

// ── Base URL ─────────────────────────────────────────────────────────────────
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001/api";

// ── Token storage key ────────────────────────────────────────────────────────
const TOKEN_KEY = "smartattend_token";

// ── Token helpers (localStorage, client-side only) ──────────────────────────
export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;

  // 1. Direct application token
  const direct = localStorage.getItem(TOKEN_KEY);
  if (direct && direct.trim()) return direct.trim();

  // 2. Supabase storage key configured in client.ts ("smartattend_supabase_auth_token")
  try {
    const supaRaw = localStorage.getItem("smartattend_supabase_auth_token");
    if (supaRaw) {
      const parsed = JSON.parse(supaRaw);
      const token = parsed?.access_token || parsed?.currentSession?.access_token;
      if (token && typeof token === "string") {
        localStorage.setItem(TOKEN_KEY, token);
        return token;
      }
    }
  } catch {}

  // 3. Fallback to default Supabase pattern (sb-*-auth-token)
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && (k.startsWith("sb-") && k.endsWith("-auth-token"))) {
        const raw = localStorage.getItem(k);
        if (raw) {
          const parsed = JSON.parse(raw);
          const token = parsed?.access_token || parsed?.currentSession?.access_token;
          if (token && typeof token === "string") {
            localStorage.setItem(TOKEN_KEY, token);
            return token;
          }
        }
      }
    }
  } catch {}

  // 4. Cookie fallback
  try {
    const match = document.cookie.match(new RegExp(`(?:^|; )${TOKEN_KEY}=([^;]*)`));
    if (match && match[1]) {
      const val = decodeURIComponent(match[1]).trim();
      if (val) return val;
    }
  } catch {}

  return null;
}

export function setStoredToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem("smartattend_supabase_auth_token");
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && (k.startsWith("sb-") && k.endsWith("-auth-token"))) {
        localStorage.removeItem(k);
      }
    }
  } catch {}
}

// ── HTTP error class ─────────────────────────────────────────────────────────
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly detail?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ── Map HTTP status codes to user-friendly messages ──────────────────────────
function statusMessage(status: number): string {
  switch (status) {
    case 400: return "Bad request. Please check your input.";
    case 401: return "Your session has expired. Please log in again.";
    case 403: return "You do not have permission to perform this action.";
    case 404: return "The requested resource was not found.";
    case 422: return "Validation error. Please check your input.";
    case 500: return "Server error. Please try again later.";
    default:  return `Request failed (${status}).`;
  }
}

// ── Core request helper ──────────────────────────────────────────────────────
async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  token?: string | null,
  isFormData?: boolean
): Promise<T> {
  const url = `${BASE_URL}${path}`;

  const headers: Record<string, string> = {};

  // Attach bearer token if available
  const resolvedToken = token ?? getStoredToken();
  if (resolvedToken) {
    headers["Authorization"] = `Bearer ${resolvedToken}`;
  }

  // Set Content-Type unless FormData (browser sets it automatically with boundary)
  if (body !== undefined && !isFormData) {
    headers["Content-Type"] = "application/json";
  }

  let fetchBody: BodyInit | undefined;
  if (body !== undefined) {
    fetchBody = isFormData ? (body as BodyInit) : JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: fetchBody,
    });
  } catch {
    throw new ApiError(0, "Unable to connect to the SmartAttend server. Please check your network.");
  }

  // Parse response body (handle empty responses like 204)
  let data: unknown;
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const detail = (data as { detail?: string })?.detail;
    throw new ApiError(
      response.status,
      detail ?? statusMessage(response.status),
      data
    );
  }

  return data as T;
}

// ── Public API methods ────────────────────────────────────────────────────────
export const api = {
  get<T>(path: string, token?: string | null): Promise<T> {
    return request<T>("GET", path, undefined, token);
  },

  post<T>(path: string, body?: unknown, token?: string | null): Promise<T> {
    return request<T>("POST", path, body, token);
  },

  put<T>(path: string, body?: unknown, token?: string | null): Promise<T> {
    return request<T>("PUT", path, body, token);
  },

  patch<T>(path: string, body?: unknown, token?: string | null): Promise<T> {
    return request<T>("PATCH", path, body, token);
  },

  delete<T>(path: string, token?: string | null): Promise<T> {
    return request<T>("DELETE", path, undefined, token);
  },

  /** Upload a file using multipart/form-data */
  upload<T>(path: string, formData: FormData, token?: string | null): Promise<T> {
    return request<T>("POST", path, formData, token, true);
  },
};

// ── Auth-specific API calls ───────────────────────────────────────────────────

/**
 * Login — FastAPI OAuth2 form-based endpoint.
 * POST /api/auth/token
 * Body: application/x-www-form-urlencoded { username, password }
 * Returns: { access_token, token_type }
 */
export async function loginRequest(
  username: string,
  password: string
): Promise<AuthTokenResponse> {
  const url = `${BASE_URL}/auth/token`;

  const body = new URLSearchParams({ username, password });

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });
  } catch {
    throw new ApiError(0, "Unable to connect to the SmartAttend server. Please check your network.");
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    if (response.status === 401 || response.status === 400) {
      throw new ApiError(response.status, "Invalid email or password.");
    }
    const detail = (data as { detail?: string })?.detail;
    throw new ApiError(response.status, detail ?? statusMessage(response.status), data);
  }

  return data as AuthTokenResponse;
}

/**
 * Get current authenticated user.
 * GET /api/auth/me
 * Requires: Authorization Bearer <token>
 */
export async function getMeRequest(token: string): Promise<AuthUser> {
  return api.get<AuthUser>("/auth/me", token);
}

/**
 * Register — Unified registration endpoint.
 * POST /api/auth/register
 */
export async function registerRequest(
  payload: RegisterPayload
): Promise<AuthTokenResponse> {
  const url = `${BASE_URL}/auth/register`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(0, "Unable to connect to the SmartAttend server. Please check your network.");
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = (data as { detail?: string })?.detail;
    throw new ApiError(response.status, detail ?? statusMessage(response.status), data);
  }

  return data as AuthTokenResponse;
}

/**
 * Link profile after native Supabase Auth signUp.
 * POST /api/auth/link-profile
 */
export async function linkProfileRequest(
  payload: RegisterPayload,
  token: string
): Promise<{ status: string; role: string; id: number }> {
  return api.post<{ status: string; role: string; id: number }>(
    "/auth/link-profile",
    payload,
    token
  );
}
