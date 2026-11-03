"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import StatCard from "@/components/StatCard";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { useAuth } from "@/context/AuthContext";
import { statsService } from "@/lib/services";
import { ApiError } from "@/lib/api";
import {
  GraduationCap,
  Calendar,
  CheckCircle2,
  XCircle,
  Radio,
  ArrowRight,
  RefreshCw,
  AlertCircle,
  ScanFace
} from "lucide-react";

export default function StudentDashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<{
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
  } | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadStudentData() {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const stats = await statsService.getStudentStats(user.id);
      setData(stats);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to connect to FastAPI /student/:id/stats endpoint.");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadStudentData();
  }, [user]);

  const percentage = data ? data.attendance_percentage : 0;
  const isAboveThreshold = percentage >= 75;

  return (
    <ProtectedPage requiredRole="student">
      <DashboardLayout
        role="student"
        title={`Student Portal — ${user?.full_name || user?.username}`}
        subtitle={`Roll Number: ${user?.student_id || user?.username || "—"} &bull; Division: ${user?.division || "AIML-B"}`}
        breadcrumbs={[{ label: "Overview" }]}
        actions={
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={loadStudentData}
              disabled={loading}
              className="p-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-[#FFD700]" : ""}`} />
            </button>
            <Link
              href="/student/profile"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#17171B] border border-[#2A2A30] hover:border-[#FFD700]/50 text-[#F5F5F5] font-semibold text-xs transition-all"
            >
              <ScanFace className="w-3.5 h-3.5 text-[#FFD700]" />
              <span>Face Biometrics</span>
            </Link>
            <Link
              href="/student/attendance"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md transition-all"
            >
              <span>Full Attendance History</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        }
      >
        {error && (
          <div className="mb-6 p-4 rounded-2xl bg-amber-950/30 border border-amber-800/60 text-amber-200 text-xs flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-[#F5F5F5]">Backend Service Notice</p>
              <p className="text-xs text-[#A1A1AA] mt-0.5">
                {error} — All student metrics reflect real authorized records without simulated numbers.
              </p>
            </div>
          </div>
        )}

        {/* Today's Campus Gate Ingress Status Banner */}
        <div className="mb-8 p-6 rounded-3xl bg-[#111114] border border-[#2A2A30] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div
              className={`w-12 h-12 rounded-2xl border flex items-center justify-center shrink-0 ${
                data?.today_rfid_checked_in
                  ? "bg-emerald-950/40 border-emerald-800/60 text-[#7BD88F]"
                  : "bg-[#17171B] border-[#2A2A30] text-[#A1A1AA]"
              }`}
            >
              <Radio className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-0.5">
                DAILY RFID GATE ARRIVAL
              </span>
              <h3 className="text-base font-bold text-[#F5F5F5]">
                {data?.today_rfid_checked_in
                  ? "Campus Gate Tap Verified Today"
                  : "No Campus Gate Tap Recorded Today"}
              </h3>
              <p className="text-xs text-[#A1A1AA] mt-0.5">
                {data?.today_rfid_checked_in
                  ? `Recorded at ${data.today_check_in_time || "Turnstile Terminal"}`
                  : "Tap your physical RFID badge at the entrance gate kiosk to register daily presence."}
              </p>
            </div>
          </div>

          <StatusBadge
            status={data?.today_rfid_checked_in ? "verified" : "pending"}
            labelOverride={data?.today_rfid_checked_in ? "Checked In" : "Not Tapped"}
          />
        </div>

        {/* 4 Attendance Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            label="Overall Attendance"
            value={`${percentage}%`}
            subtext={isAboveThreshold ? "Above 75% Statutory Cutoff" : "Below 75% Attendance Warning"}
            trend={isAboveThreshold ? "Standing: Compliant" : "Defaulter Risk"}
            trendPositive={isAboveThreshold}
            icon={GraduationCap}
          />
          <StatCard
            label="Total Eligible Lectures"
            value={data ? data.total_lectures : 0}
            subtext="Sessions held in division"
            icon={Calendar}
          />
          <StatCard
            label="Attended Lectures"
            value={data ? data.present_count : 0}
            subtext="Verified present"
            icon={CheckCircle2}
          />
          <StatCard
            label="Absences Logged"
            value={data ? data.absent_count : 0}
            subtext="Recorded absent"
            icon={XCircle}
          />
        </div>

        {/* Recent Lecture History */}
        <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7 shadow-xl mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                SESSION LEDGER
              </span>
              <h3 className="text-lg font-bold text-[#F5F5F5]">My Recent Lecture Sessions</h3>
            </div>
            <Link
              href="/student/attendance"
              className="text-xs text-[#FFD700] hover:text-[#FFE34D] flex items-center gap-1 font-semibold"
            >
              <span>View Full History</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {loading ? (
            <div className="py-12 text-center text-xs text-[#A1A1AA]">
              <RefreshCw className="w-5 h-5 animate-spin text-[#FFD700] mx-auto mb-2" />
              <span>Querying verified student records...</span>
            </div>
          ) : !data || data.recent_records.length === 0 ? (
            <EmptyState
              icon={Calendar}
              title="No Attendance Records Logged"
              description="No finalized lecture attendance records have been published for your profile yet."
            />
          ) : (
            <div className="space-y-3">
              {data.recent_records.map((rec, i) => (
                <div
                  key={i}
                  className="bg-[#17171B] border border-[#2A2A30] rounded-2xl p-4 flex items-center justify-between gap-4"
                >
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-[#F5F5F5]">{rec.subject}</span>
                      <span className="text-[#2A2A30]">&bull;</span>
                      <span className="text-xs text-[#A1A1AA]">{rec.date}</span>
                    </div>
                    <span className="text-[11px] text-[#A1A1AA]">Faculty: {rec.teacher_name}</span>
                  </div>

                  <StatusBadge status={rec.status.toLowerCase()} />
                </div>
              ))}
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedPage>
  );
}
