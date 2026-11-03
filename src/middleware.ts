/**
 * AIoT SmartAttend — Route Protection Middleware
 *
 * Edge runtime middleware ensuring:
 * - Public routes: /, /login, /forgot-password, /auth/callback, /kiosk, /unauthorized
 * - Role-specific route boundaries: /admin, /teacher, /student, /parent
 */

import { NextResponse, NextRequest } from "next/server";

const PROTECTED: Array<{ prefix: string; role: string }> = [
  { prefix: "/admin",   role: "admin"   },
  { prefix: "/teacher", role: "teacher" },
  { prefix: "/student", role: "student" },
  { prefix: "/parent",  role: "parent"  },
];

const PUBLIC_PATHS = [
  "/",
  "/login",
  "/forgot-password",
  "/auth/callback",
  "/kiosk",
  "/unauthorized",
];

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
    const json = atob(padded);
    return JSON.parse(json) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function extractUserRole(payload: Record<string, unknown>): string {
  const directRole = typeof payload["role"] === "string" ? payload["role"].toLowerCase() : "";
  if (directRole && directRole !== "authenticated") {
    return directRole;
  }

  // Supabase GoTrue sets role="authenticated" and stores institutional role in user_metadata or app_metadata
  const userMeta = (payload["user_metadata"] as Record<string, unknown>) || {};
  const appMeta = (payload["app_metadata"] as Record<string, unknown>) || {};
  const metaRole = (
    (typeof userMeta["role"] === "string" ? userMeta["role"] : "") ||
    (typeof appMeta["role"] === "string" ? appMeta["role"] : "")
  ).toLowerCase();

  if (metaRole) {
    return metaRole;
  }

  const email = (typeof payload["email"] === "string" ? payload["email"] : "").toLowerCase();
  if (email === "admin@smartattend.edu") {
    return "admin";
  }

  return directRole;
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 1. Always allow public paths exactly or as prefix
  if (PUBLIC_PATHS.some((p) => pathname === p || (p !== "/" && pathname.startsWith(p + "/")))) {
    return NextResponse.next();
  }

  // 2. Check if route is protected
  const rule = PROTECTED.find((r) => pathname === r.prefix || pathname.startsWith(r.prefix + "/"));
  if (!rule) {
    return NextResponse.next();
  }

  // 3. Inspect token cookie
  const token = request.cookies.get("smartattend_token")?.value;
  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // 4. Decode payload
  const payload = decodeJwtPayload(token);
  if (!payload) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // 5. Expiration check
  const exp = payload["exp"];
  if (typeof exp === "number" && Date.now() / 1000 > exp) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    const res = NextResponse.redirect(loginUrl);
    res.cookies.delete("smartattend_token");
    return res;
  }

  // 6. Role check (supporting Supabase metadata and admin supervisor privileges)
  const userRole = extractUserRole(payload);
  const targetRole = rule.role.toLowerCase();

  if (!userRole || (userRole !== targetRole && userRole !== "admin")) {
    return NextResponse.redirect(new URL("/unauthorized", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.svg|.*\\.png|.*\\.jpg|.*\\.ico).*)",
  ],
};
