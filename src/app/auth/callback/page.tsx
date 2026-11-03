"use client";

import React, { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Logo from "@/components/Logo";
import { Loader2, AlertCircle, CheckCircle2, Lock, ArrowRight } from "lucide-react";
import Link from "next/link";
import { supabase } from "@/lib/supabase/client";
import { getMeRequest, setStoredToken } from "@/lib/api";
import { ROLE_HOME, UserRole } from "@/types/auth";

export default function AuthCallbackPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isRecovery, setIsRecovery] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [updating, setUpdating] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState(false);

  useEffect(() => {
    async function processCallback() {
      try {
        if (typeof window === "undefined") return;

        const hash = window.location.hash.substring(1);
        const search = window.location.search.substring(1);
        const params = new URLSearchParams(hash || search);

        let token = params.get("access_token") || params.get("token");
        const type = params.get("type");

        if (!token) {
          const { data: sessionData } = await supabase.auth.getSession();
          token = sessionData?.session?.access_token || null;
        }

        if (!token) {
          throw new Error("No authentication token was returned from the identity provider.");
        }

        // Check if this is a password recovery link
        if (type === "recovery" || hash.includes("type=recovery") || search.includes("type=recovery")) {
          setIsRecovery(true);
          setStoredToken(token);
          const expires = new Date(Date.now() + 8 * 60 * 60 * 1000).toUTCString();
          document.cookie = `smartattend_token=${token}; path=/; expires=${expires}; SameSite=Lax`;
          return;
        }

        // Validate and store normal login/confirmation session
        const me = await getMeRequest(token);
        if (!me || me.is_active === false) {
          throw new Error("Account is inactive or could not be verified.");
        }

        setStoredToken(token);
        const expires = new Date(Date.now() + 8 * 60 * 60 * 1000).toUTCString();
        document.cookie = `smartattend_token=${token}; path=/; expires=${expires}; SameSite=Lax`;

        const dest = ROLE_HOME[me.role as UserRole] ?? "/admin";
        router.push(dest);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to complete authentication callback.");
      }
    }

    processCallback();
  }, [router]);

  async function handlePasswordUpdate(e: FormEvent) {
    e.preventDefault();
    if (updating) return;

    if (newPassword.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setUpdating(true);
    setError(null);

    try {
      const { error: supaErr } = await supabase.auth.updateUser({ password: newPassword });
      if (supaErr) {
        throw new Error(supaErr.message);
      }

      setUpdateSuccess(true);
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update password.");
    } finally {
      setUpdating(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0B0B0D] text-[#F5F5F5] flex flex-col items-center justify-center p-6 text-center">
      <Logo size="lg" />

      {isRecovery ? (
        <div className="mt-8 max-w-md w-full p-8 rounded-3xl bg-[#111114] border border-[#2A2A30] text-left shadow-2xl">
          <div className="text-center mb-6">
            <div className="w-12 h-12 rounded-full bg-[#FFD700]/10 border border-[#FFD700]/20 text-[#FFD700] flex items-center justify-center mx-auto mb-3">
              <Lock className="w-6 h-6" />
            </div>
            <h2 className="text-xl font-bold text-[#F5F5F5]">Set New Password</h2>
            <p className="text-xs text-[#A1A1AA] mt-1">
              Enter your new password to regain access to your SmartAttend account.
            </p>
          </div>

          {updateSuccess ? (
            <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/60 text-[#7BD88F] text-xs flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 shrink-0" />
              <span>Password updated successfully! Redirecting to login...</span>
            </div>
          ) : (
            <>
              {error && (
                <div className="mb-4 p-3.5 rounded-xl bg-red-950/40 border border-red-800/60 text-red-200 text-xs flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handlePasswordUpdate} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">New Password</label>
                  <input
                    type="password"
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter at least 6 characters"
                    className="w-full h-11 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Confirm New Password</label>
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Repeat new password"
                    className="w-full h-11 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={updating}
                  className="w-full h-11 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {updating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Updating Password...</span>
                    </>
                  ) : (
                    <>
                      <span>Update Password</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            </>
          )}
        </div>
      ) : error ? (
        <div className="mt-8 max-w-md p-6 rounded-2xl bg-[#17171B] border border-red-800/60 text-red-200">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-[#F5F5F5] mb-2">Authentication Callback Failed</h2>
          <p className="text-xs text-[#A1A1AA] mb-6 leading-relaxed">{error}</p>
          <Link
            href="/login"
            className="inline-flex items-center justify-center px-6 py-2.5 rounded-full bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
          >
            Return to Sign In
          </Link>
        </div>
      ) : (
        <div className="mt-8 flex flex-col items-center gap-3 text-[#A1A1AA]">
          <Loader2 className="w-6 h-6 animate-spin text-[#FFD700]" />
          <p className="text-sm font-medium">Verifying authorization and configuring workspace...</p>
        </div>
      )}
    </div>
  );
}
