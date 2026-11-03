"use client";

/**
 * AIoT SmartAttend — Native Supabase Authentication & Session Management
 */

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase/client";
import {
  loginRequest,
  registerRequest,
  linkProfileRequest,
  getMeRequest,
  setStoredToken,
  getStoredToken,
  clearStoredToken,
  ApiError,
} from "@/lib/api";
import type { AuthUser, AuthContextValue, UserRole, RegisterPayload } from "@/types/auth";
import { ROLE_HOME } from "@/types/auth";

const COOKIE_KEY = "smartattend_token";

function setCookie(value: string) {
  if (typeof document === "undefined") return;
  const expires = new Date(Date.now() + 8 * 60 * 60 * 1000).toUTCString();
  document.cookie = `${COOKIE_KEY}=${value}; path=/; expires=${expires}; SameSite=Lax`;
}

function deleteCookie() {
  if (typeof document === "undefined") return;
  document.cookie = `${COOKIE_KEY}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();

  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore and synchronize session
  useEffect(() => {
    let isMounted = true;

    async function restoreSession() {
      try {
        // 1. Try Supabase session first
        let activeSupaToken: string | undefined = undefined;
        try {
          const { data: supaSessionData } = await supabase.auth.getSession();
          activeSupaToken = supaSessionData?.session?.access_token;
        } catch {
          // Supabase unreachable or offline
        }

        const effectiveToken = activeSupaToken || getStoredToken();

        if (!effectiveToken) {
          if (isMounted) setIsLoading(false);
          return;
        }

        const me = await getMeRequest(effectiveToken);
        if (!me || me.is_active === false) {
          throw new Error("Inactive or unlinked account");
        }

        const normRole = (me.role ? String(me.role).toLowerCase() : "student") as UserRole;
        if (isMounted) {
          setStoredToken(effectiveToken);
          setCookie(effectiveToken);
          setToken(effectiveToken);
          setUser({ ...me, role: normRole });
        }
      } catch (err) {
        if (isMounted) {
          clearStoredToken();
          deleteCookie();
          setToken(null);
          setUser(null);
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    restoreSession();

    // 2. Subscribe to Supabase Auth state changes
    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (event === "SIGNED_OUT") {
          clearStoredToken();
          deleteCookie();
          if (isMounted) {
            setToken(null);
            setUser(null);
          }
        } else if (session?.access_token && (event === "SIGNED_IN" || event === "TOKEN_REFRESHED")) {
          try {
            const me = await getMeRequest(session.access_token);
            if (me && me.is_active !== false) {
              const normRole = (me.role ? String(me.role).toLowerCase() : "student") as UserRole;
              if (isMounted) {
                setStoredToken(session.access_token);
                setCookie(session.access_token);
                setToken(session.access_token);
                setUser({ ...me, role: normRole });
              }
            }
          } catch {
            // Ignore background refresh errors
          }
        }
      }
    );

    return () => {
      isMounted = false;
      authListener.subscription.unsubscribe();
    };
  }, []);

  // Login handler
  const login = useCallback(
    async (username: string, password: string, requestedRole?: UserRole) => {
      const cleanUsername = username.trim();

      // Authenticate directly through FastAPI backend
      const res = await loginRequest(cleanUsername, password);
      const resolvedToken = res.access_token;

      if (!resolvedToken) {
        throw new ApiError(401, "Authentication failed. Could not obtain session token.");
      }

      // Verify user identity and role strictly from server-side database records
      const me = await getMeRequest(resolvedToken);

      if (!me) {
        throw new ApiError(401, "Failed to verify account identity from server.");
      }

      if (me.is_active === false) {
        throw new ApiError(403, "This account is deactivated. Please contact your institution administrator.");
      }

      const normRole = (me.role ? String(me.role).toLowerCase() : "student") as UserRole;
      const normalizedMe: AuthUser = {
        ...me,
        role: normRole,
      };

      setStoredToken(resolvedToken);
      setCookie(resolvedToken);
      setToken(resolvedToken);
      setUser(normalizedMe);

      // Redirect to authorized portal
      const destination = ROLE_HOME[normRole] ?? "/admin";
      router.push(destination);
    },
    [router]
  );

  // Register handler
  const register = useCallback(
    async (payload: RegisterPayload) => {
      // 1. Strict Role Restriction: Public registration must never grant ADMIN privileges
      if (payload.role.toLowerCase() === "admin") {
        throw new ApiError(403, "Public registration cannot create Administrator accounts.");
      }

      const targetEmail = (
        payload.email ||
        (payload.roll_no ? `${payload.roll_no.toLowerCase()}@student.smartattend.edu` : "")
      ).trim().toLowerCase();

      if (!targetEmail || !targetEmail.includes("@")) {
        throw new ApiError(400, "A valid email address is required for registration.");
      }

      // 2. Register via the centralized backend API
      const res = await registerRequest({ ...payload, email: targetEmail });
      const effectiveToken = res.access_token;

      if (!effectiveToken) {
        throw new ApiError(400, "Registration failed to establish an active session.");
      }

      // 3. Retrieve verified profile
      const me = await getMeRequest(effectiveToken);
      if (!me) {
        throw new ApiError(401, "Account registered, but profile verification failed.");
      }

      const normRole = (me.role ? String(me.role).toLowerCase() : payload.role.toLowerCase()) as UserRole;
      const normalizedMe: AuthUser = {
        ...me,
        role: normRole,
      };

      setStoredToken(effectiveToken);
      setCookie(effectiveToken);
      setToken(effectiveToken);
      setUser(normalizedMe);

      const destination = ROLE_HOME[normRole] ?? "/admin";
      router.push(destination);
    },
    [router]
  );

  // Logout handler
  const logout = useCallback(async () => {
    try {
      await supabase.auth.signOut();
    } catch {
      // Ignore network errors on logout
    }
    clearStoredToken();
    deleteCookie();
    setToken(null);
    setUser(null);
    router.push("/login");
  }, [router]);

  // Password Reset handler
  const resetPassword = useCallback(async (email: string) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email.trim().toLowerCase(), {
      redirectTo: typeof window !== "undefined" ? `${window.location.origin}/auth/callback?type=recovery` : undefined,
    });
    if (error) {
      throw new ApiError(400, error.message);
    }
  }, []);

  const value: AuthContextValue = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user && !!token,
    login,
    register,
    logout,
    resetPassword,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return ctx;
}
