"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import StatCard from "@/components/StatCard";
import EmptyState from "@/components/EmptyState";
import { statsService, SystemStats } from "@/lib/services";
import { ApiError } from "@/lib/api";
import {
  GraduationCap,
  Users,
  UserCheck,
  BookOpen,
  TrendingUp,
  AlertTriangle,
  Radio,
  ArrowRight,
  RefreshCw,
  PlusCircle,
  FileSpreadsheet,
  Layers,
  Settings,
  AlertCircle
} from "lucide-react";

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function fetchStats() {
    setLoading(true);
    setError(null);
    try {
      const data = await statsService.getAdminStats();
      setStats(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to connect to FastAPI /admin/stats endpoint.");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <ProtectedPage requiredRole="admin">
      <DashboardLayout
        role="admin"
        title="Institutional Command Center"
        subtitle="Live oversight of campus check-ins, faculty lecture sessions, and verification records."
        actions={
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={fetchStats}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#17171B] hover:bg-[#1F1F24] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-[#FFD700]" : ""}`} />
              <span>Refresh Data</span>
            </button>
            <Link
              href="/admin/students"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-[0_0_15px_rgba(255,215,0,0.2)] transition-all"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Manage Campus</span>
            </Link>
          </div>
        }
      >
        {/* Backend Status / Connection Notice */}
        {error && (
          <div className="mb-6 p-4 rounded-2xl bg-amber-950/30 border border-amber-800/60 text-amber-200 text-xs sm:text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-bold text-[#F5F5F5]">Backend Service Notice</p>
              <p className="text-xs text-[#A1A1AA] mt-1">
                {error} - Live statistics require the FastAPI endpoint at <code className="text-[#FFD700]">/api/admin/stats</code>.
                Displaying zero-baseline metrics per strict No-Dummy-Data policy.
              </p>
            </div>
          </div>
        )}

        {/* 6 Key Institution Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
          <StatCard
            label="Total Students"
            value={loading ? "..." : stats ? String(stats.total_students) : "0"}
            subtext="Enrolled in Supabase"
            icon={GraduationCap}
          />
          <StatCard
            label="Active Faculty"
            value={loading ? "..." : stats ? String(stats.total_teachers) : "0"}
            subtext="Active in Supabase"
            icon={Users}
          />
          <StatCard
            label="Daily Check-Ins"
            value={loading ? "..." : stats ? String(stats.today_checkins) : "0"}
            subtext="RFID gateway taps today"
            icon={UserCheck}
          />
          <StatCard
            label="Today's Lectures"
            value={loading ? "..." : stats ? String(stats.today_lectures) : "0"}
            subtext="Timetabled sessions"
            icon={BookOpen}
          />
          <StatCard
            label="Attendance Rate"
            value={
              loading
                ? "..."
                : stats && stats.overall_attendance_rate !== null && stats.overall_attendance_rate !== undefined
                ? `${stats.overall_attendance_rate}%`
                : "N/A"
            }
            subtext={
              stats && stats.overall_attendance_rate !== null && stats.overall_attendance_rate !== undefined
                ? "Institutional average"
                : "No finalized records"
            }
            icon={TrendingUp}
          />
          <StatCard
            label="Review Pending"
            value={loading ? "..." : stats ? String(stats.pending_flagged_cases) : "0"}
            subtext="Flagged attendance cases"
            icon={AlertTriangle}
          />
        </div>

        {/* Institutional Management Hub Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
          {/* Quick Operations Modules */}
          <div className="lg:col-span-8 bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7">
            <div className="flex items-center justify-between mb-6">
              <div>
                <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                  CORE INFRASTRUCTURE
                </span>
                <h3 className="text-lg font-bold text-[#F5F5F5]">Management Workflows</h3>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Link
                href="/admin/students"
                className="bg-[#17171B] border border-[#2A2A30] hover:border-[#FFD700]/50 rounded-2xl p-5 transition-all group flex flex-col justify-between"
              >
                <div>
                  <div className="w-10 h-10 rounded-xl bg-[#111114] border border-[#2A2A30] text-[#FFD700] flex items-center justify-center mb-3 group-hover:border-[#FFD700]/40 transition-colors">
                    <GraduationCap className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-bold text-[#F5F5F5] group-hover:text-[#FFD700] transition-colors">
                    Student Management
                  </h4>
                  <p className="text-xs text-[#A1A1AA] mt-1 leading-relaxed">
                    Register students, assign division cohorts, and pair RFID card identifiers.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-[#2A2A30]/60 flex items-center justify-between text-xs text-[#FFD700]">
                  <span>Open Directory</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </Link>

              <Link
                href="/admin/teachers"
                className="bg-[#17171B] border border-[#2A2A30] hover:border-[#FFD700]/50 rounded-2xl p-5 transition-all group flex flex-col justify-between"
              >
                <div>
                  <div className="w-10 h-10 rounded-xl bg-[#111114] border border-[#2A2A30] text-[#FFD700] flex items-center justify-center mb-3 group-hover:border-[#FFD700]/40 transition-colors">
                    <Users className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-bold text-[#F5F5F5] group-hover:text-[#FFD700] transition-colors">
                    Faculty Directory
                  </h4>
                  <p className="text-xs text-[#A1A1AA] mt-1 leading-relaxed">
                    Manage professor assignments, department roles, and class attendance permissions.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-[#2A2A30]/60 flex items-center justify-between text-xs text-[#FFD700]">
                  <span>Open Faculty</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </Link>

              <Link
                href="/admin/classes"
                className="bg-[#17171B] border border-[#2A2A30] hover:border-[#FFD700]/50 rounded-2xl p-5 transition-all group flex flex-col justify-between"
              >
                <div>
                  <div className="w-10 h-10 rounded-xl bg-[#111114] border border-[#2A2A30] text-[#FFD700] flex items-center justify-center mb-3 group-hover:border-[#FFD700]/40 transition-colors">
                    <Layers className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-bold text-[#F5F5F5] group-hover:text-[#FFD700] transition-colors">
                    Classes & Divisions
                  </h4>
                  <p className="text-xs text-[#A1A1AA] mt-1 leading-relaxed">
                    Configure semester batches, departments, curricula, and division student caps.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-[#2A2A30]/60 flex items-center justify-between text-xs text-[#FFD700]">
                  <span>Manage Classes</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </Link>

              <Link
                href="/admin/devices"
                className="bg-[#17171B] border border-[#2A2A30] hover:border-[#FFD700]/50 rounded-2xl p-5 transition-all group flex flex-col justify-between"
              >
                <div>
                  <div className="w-10 h-10 rounded-xl bg-[#111114] border border-[#2A2A30] text-[#FFD700] flex items-center justify-center mb-3 group-hover:border-[#FFD700]/40 transition-colors">
                    <Radio className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-bold text-[#F5F5F5] group-hover:text-[#FFD700] transition-colors">
                    RFID Gateway Devices
                  </h4>
                  <p className="text-xs text-[#A1A1AA] mt-1 leading-relaxed">
                    Monitor ESP8266 + RC522 attendance kiosks, network heartbeats, and gate locations.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-[#2A2A30]/60 flex items-center justify-between text-xs text-[#FFD700]">
                  <span>Inspect Hardware</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </Link>
            </div>
          </div>

          {/* Right Column: Institutional Security & System Links */}
          <div className="lg:col-span-4 space-y-6">
            <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7">
              <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                EXECUTIVE REPORTS
              </span>
              <h3 className="text-base font-bold text-[#F5F5F5] mb-2">Audit & Analytics</h3>
              <p className="text-xs text-[#A1A1AA] leading-relaxed mb-6">
                Generate official attendance ledgers and CSV records directly from verified database entries.
              </p>

              <div className="space-y-3">
                <Link
                  href="/admin/attendance"
                  className="flex items-center justify-between p-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#F5F5F5] hover:border-[#FFD700]/40 transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <UserCheck className="w-4 h-4 text-[#FFD700]" />
                    <span>Campus Attendance Logs</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-[#A1A1AA]" />
                </Link>

                <Link
                  href="/admin/reports"
                  className="flex items-center justify-between p-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#F5F5F5] hover:border-[#FFD700]/40 transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <FileSpreadsheet className="w-4 h-4 text-[#FFD700]" />
                    <span>Generate Official Reports</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-[#A1A1AA]" />
                </Link>

                <Link
                  href="/admin/settings"
                  className="flex items-center justify-between p-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#F5F5F5] hover:border-[#FFD700]/40 transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <Settings className="w-4 h-4 text-[#FFD700]" />
                    <span>Institutional Settings</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-[#A1A1AA]" />
                </Link>
              </div>
            </div>

            {/* Hardware Kiosk Launcher Card */}
            <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7 relative overflow-hidden">
              <div className="flex items-center gap-2 text-xs font-bold text-[#FFD700] mb-2">
                <Radio className="w-4 h-4" />
                <span>IOT GATEWAY CONNECTOR</span>
              </div>
              <h4 className="text-sm font-bold text-[#F5F5F5]">Hardware Kiosk Display</h4>
              <p className="text-xs text-[#A1A1AA] mt-1 mb-4 leading-relaxed">
                Launch the dedicated hardware screen for students tapping RFID badges at the physical terminal.
              </p>
              <Link
                href="/kiosk"
                target="_blank"
                className="inline-flex items-center justify-center w-full py-2.5 px-4 rounded-xl bg-[#17171B] hover:bg-[#1F1F24] border border-[#FFD700]/40 text-xs font-bold text-[#FFD700] transition-colors"
              >
                Launch Kiosk Interface ↗
              </Link>
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedPage>
  );
}
