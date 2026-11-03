"use client";

import React, { useState, type FormEvent } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { ApiError } from "@/lib/api";
import Logo from "@/components/Logo";
import type { UserRole } from "@/types/auth";
import {
  Eye,
  EyeOff,
  Lock,
  User,
  AlertCircle,
  Loader2,
  ArrowRight,
  Shield,
  GraduationCap,
  Users,
  Building,
  Radio,
} from "lucide-react";

const ROLES: Array<{
  id: UserRole;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  hint: string;
}> = [
  { id: "admin", label: "Admin", icon: Building, hint: "Administrator username or email" },
  { id: "teacher", label: "Teacher", icon: Shield, hint: "Faculty ID or institutional email" },
  { id: "student", label: "Student", icon: GraduationCap, hint: "Student PRN / Roll number or email" },
  { id: "parent", label: "Parent", icon: Users, hint: "Registered guardian email or mobile ID" },
];

export default function LoginPage() {
  const { login, isLoading: sessionLoading, isAuthenticated, user } = useAuth();

  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (isSubmitting) return;

    setError(null);
    setIsSubmitting(true);

    try {
      await login(username.trim(), password, selectedRole || undefined);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Unable to authenticate with SmartAttend backend. Please check connection.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  if (sessionLoading) {
    return (
      <div className="min-h-screen bg-[#0B0B0D] flex flex-col items-center justify-center gap-4 text-[#A1A1AA]">
        <Logo size="lg" />
        <div className="flex items-center gap-2 text-sm">
          <Loader2 className="w-4 h-4 animate-spin text-[#FFD700]" />
          <span>Verifying session credentials...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0B0D] text-[#F5F5F5] flex flex-col justify-between p-6 sm:p-10 font-sans selection:bg-[#FFD700]/30 selection:text-[#FFD700]">
      {/* Top Bar with Home Link & Kiosk Shortcut */}
      <div className="max-w-[1240px] w-full mx-auto flex items-center justify-between">
        <Logo size="md" href="/" />

        <div className="flex items-center gap-4 text-xs font-medium">
          <Link
            href="/kiosk"
            className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#17171B] border border-[#2A2A30] text-[#A1A1AA] hover:text-[#FFD700] hover:border-[#C9A227]/40 transition-colors"
          >
            <Radio className="w-3.5 h-3.5 text-[#FFD700]" />
            <span>RFID Kiosk Screen</span>
          </Link>
          <Link
            href="/signup"
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-[#FFD700]/10 border border-[#FFD700]/30 text-[#FFD700] hover:bg-[#FFD700]/20 font-bold transition-all"
          >
            <span>Sign Up</span>
          </Link>
          <Link
            href="/"
            className="text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors"
          >
            ← Back to Overview
          </Link>
        </div>
      </div>

      {/* Main Login Card */}
      <div className="w-full max-w-[460px] mx-auto my-auto py-8">
        <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-7 sm:p-9 shadow-[0_30px_80px_-20px_rgba(0,0,0,0.9)]">
          {/* Header */}
          <div className="text-center mb-7">
            <span className="text-[11px] font-bold text-[#FFD700] tracking-[0.18em] uppercase block mb-2">
              AUTHENTICATION PORTAL
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F5F5F5] font-display">
              Sign In to SmartAttend
            </h1>
            <p className="text-xs sm:text-sm text-[#A1A1AA] mt-2">
              Enter your verified credentials to access your institutional workspace.
            </p>
          </div>

          {/* Role Preference Filter (Optional Visual Helper) */}
          <div className="mb-6">
            <label className="text-[11px] font-semibold text-[#A1A1AA] tracking-wider uppercase block mb-2">
              Select Your Role Profile
            </label>
            <div className="grid grid-cols-4 gap-2">
              {ROLES.map((role) => {
                const IconComponent = role.icon;
                const isSelected = selectedRole === role.id;
                return (
                  <button
                    key={role.id}
                    type="button"
                    onClick={() => setSelectedRole(isSelected ? null : role.id)}
                    className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-xs font-semibold transition-all ${
                      isSelected
                        ? "bg-[#17171B] border-[#FFD700] text-[#FFD700] shadow-[0_0_12px_rgba(255,215,0,0.15)]"
                        : "bg-[#17171B]/60 border-[#2A2A30] text-[#A1A1AA] hover:text-[#F5F5F5] hover:border-[#2A2A30]"
                    }`}
                  >
                    <IconComponent className="w-4 h-4 mb-1" />
                    <span className="text-[11px]">{role.label}</span>
                  </button>
                );
              })}
            </div>
            <p className="text-[10px] text-[#A1A1AA]/70 mt-1.5 text-center">
              *Visual role selection does not grant permissions. All claims are verified against the backend.
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div
              role="alert"
              className="mb-6 p-3.5 rounded-xl bg-red-950/40 border border-red-800/60 text-red-200 text-xs sm:text-[13px] flex items-start gap-2.5"
            >
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 leading-snug">{error}</div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {/* Username / Email */}
            <div>
              <label
                htmlFor="username"
                className="text-xs font-semibold text-[#F5F5F5] block mb-1.5"
              >
                Username or Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#A1A1AA]">
                  <User className="w-4 h-4" />
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder={
                    selectedRole
                      ? ROLES.find((r) => r.id === selectedRole)?.hint
                      : "e.g. roll number or email"
                  }
                  disabled={isSubmitting}
                  className="w-full h-11 pl-10 pr-4 rounded-xl bg-[#17171B] border border-[#2A2A30] text-sm text-[#F5F5F5] placeholder-[#A1A1AA]/50 focus:border-[#FFD700] focus:ring-1 focus:ring-[#FFD700] focus:outline-none transition-colors disabled:opacity-50"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="password"
                  className="text-xs font-semibold text-[#F5F5F5]"
                >
                  Password
                </label>
                <Link
                  href="/forgot-password"
                  className="text-xs text-[#FFD700] hover:text-[#FFE34D] transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#A1A1AA]">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  disabled={isSubmitting}
                  className="w-full h-11 pl-10 pr-11 rounded-xl bg-[#17171B] border border-[#2A2A30] text-sm text-[#F5F5F5] placeholder-[#A1A1AA]/50 focus:border-[#FFD700] focus:ring-1 focus:ring-[#FFD700] focus:outline-none transition-colors disabled:opacity-50"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting || !username.trim() || !password}
                className="w-full h-12 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-sm tracking-wide flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(255,215,0,0.25)] transition-all transform active:scale-[0.99] disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-[#0B0B0D]" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>

            {/* Sign Up Redirect Link */}
            <div className="mt-5 text-center text-xs text-[#A1A1AA]">
              <span>Don't have an institutional account? </span>
              <Link
                href="/signup"
                className="text-[#FFD700] hover:text-[#FFE34D] font-bold hover:underline transition-colors"
              >
                Sign Up
              </Link>
            </div>
          </form>

          {/* Security & Backend Notice */}
          <div className="mt-7 pt-5 border-t border-[#2A2A30]/60 text-center text-xs text-[#A1A1AA]">
            <p>
              Protected by FastAPI JWT & Supabase Row Level Security.
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="max-w-[1240px] w-full mx-auto text-center text-xs text-[#A1A1AA]/60">
        AIoT SmartAttend Attendance System &bull; Secure Institutional Access
      </div>
    </div>
  );
}
