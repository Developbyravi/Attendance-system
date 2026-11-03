"use client";

import Link from "next/link";
import Logo from "@/components/Logo";
import { useAuth } from "@/context/AuthContext";
import { ROLE_HOME, ROLE_DISPLAY } from "@/types/auth";
import type { UserRole } from "@/types/auth";
import { ShieldAlert, ArrowRight, LogOut, Home } from "lucide-react";

export default function UnauthorizedPage() {
  const { user, logout } = useAuth();

  const normUserRole  = user?.role ? String(user.role).toLowerCase() : "";
  const dashboardHref = user ? (ROLE_HOME[normUserRole] ?? `/${normUserRole}` ?? "/") : "/login";
  const displayRole   = user ? (ROLE_DISPLAY[normUserRole] ?? user.role) : null;

  return (
    <div className="min-h-screen bg-[#0B0B0D] text-[#F5F5F5] flex flex-col items-center justify-center p-6 text-center font-sans">
      <Logo size="md" href="/" />

      <div className="w-full max-w-md bg-[#111114] border border-[#2A2A30] rounded-3xl p-8 sm:p-9 shadow-2xl mt-8">
        <div className="w-14 h-14 rounded-2xl bg-red-950/40 border border-red-800/60 text-red-400 flex items-center justify-center mx-auto mb-5">
          <ShieldAlert className="w-7 h-7" />
        </div>

        <h1 className="text-2xl font-extrabold text-[#F5F5F5] font-display">
          Access Restricted
        </h1>

        <p className="text-xs sm:text-sm text-[#A1A1AA] mt-2 mb-6 leading-relaxed">
          {user
            ? `Your account is authenticated as ${displayRole}. You do not have permission to view this section.`
            : "You must be authenticated with the proper role to view this page."}
        </p>

        <div className="space-y-3">
          {user ? (
            <Link
              href={dashboardHref}
              className="w-full h-11 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs tracking-wider flex items-center justify-center gap-2 transition-all shadow-[0_0_15px_rgba(255,215,0,0.2)]"
            >
              <span>RETURN TO MY DASHBOARD</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          ) : (
            <Link
              href="/login"
              className="w-full h-11 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs tracking-wider flex items-center justify-center gap-2 transition-all"
            >
              <span>SIGN IN</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          )}

          <div className="flex items-center gap-2">
            <Link
              href="/"
              className="flex-1 h-10 rounded-xl bg-[#17171B] hover:bg-[#1F1F24] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA] hover:text-[#F5F5F5] flex items-center justify-center gap-1.5 transition-colors"
            >
              <Home className="w-3.5 h-3.5" />
              <span>Overview</span>
            </Link>
            {user && (
              <button
                type="button"
                onClick={logout}
                className="flex-1 h-10 rounded-xl bg-[#17171B] hover:bg-red-950/30 border border-[#2A2A30] text-xs font-semibold text-red-400 flex items-center justify-center gap-1.5 transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            )}
          </div>
        </div>
      </div>

      <p className="mt-8 text-xs text-[#A1A1AA]/60">
        AIoT SmartAttend Security Protocol &bull; Enforced by FastAPI & Supabase RLS
      </p>
    </div>
  );
}
