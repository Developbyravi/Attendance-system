"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { useAuth } from "@/context/AuthContext";
import { lectureService, LectureSession } from "@/lib/services";
import { ApiError } from "@/lib/api";
import {
  History,
  BookOpen,
  Calendar,
  Clock,
  ArrowRight,
  RefreshCw,
  AlertCircle,
  PlusCircle,
} from "lucide-react";

export default function TeacherAttendanceHistoryPage() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<LectureSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [dateFilter, setDateFilter] = useState("");

  async function loadHistory() {
    setLoading(true);
    setError(null);
    try {
      const data = await lectureService.getAll({
        teacher_id: user?.id,
        date: dateFilter || undefined,
      });
      setSessions(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to connect to FastAPI /lectures endpoint.");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, [dateFilter, user]);

  return (
    <ProtectedPage requiredRole="teacher">
      <DashboardLayout
        role="teacher"
        title="Attendance Session Ledgers"
        subtitle="Review locked past session registers, attendance percentages, and historical records."
        breadcrumbs={[{ label: "Attendance History" }]}
        actions={
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={loadHistory}
              disabled={loading}
              className="p-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-[#FFD700]" : ""}`} />
            </button>
            <Link
              href="/teacher/lectures/new"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md transition-all"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Create Lecture</span>
            </Link>
          </div>
        }
      >
        <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-4 mb-6 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs">
            <Calendar className="w-4 h-4 text-[#FFD700]" />
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="h-10 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
            />
            {dateFilter && (
              <button
                type="button"
                onClick={() => setDateFilter("")}
                className="text-xs text-[#A1A1AA] hover:text-[#F5F5F5] ml-2"
              >
                Clear
              </button>
            )}
          </div>
          <span className="text-xs text-[#A1A1AA]">
            Recorded sessions: <strong className="text-[#F5F5F5]">{sessions.length}</strong>
          </span>
        </div>

        {loading ? (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-12 text-center text-xs text-[#A1A1AA]">
            <RefreshCw className="w-5 h-5 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Loading historical attendance registers...</span>
          </div>
        ) : error ? (
          <EmptyState
            icon={AlertCircle}
            title="Database Connection Notice"
            description={`${error} No dummy sessions are injected.`}
            action={
              <button
                type="button"
                onClick={loadHistory}
                className="px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
              >
                Retry
              </button>
            }
          />
        ) : sessions.length === 0 ? (
          <EmptyState
            icon={History}
            title="No Past Attendance Ledgers"
            description="No lecture sessions were found for the selected date criteria. Create a lecture session to begin recording attendance."
            action={
              <Link
                href="/teacher/lectures/new"
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
              >
                <PlusCircle className="w-4 h-4" />
                <span>Create Lecture</span>
              </Link>
            }
          />
        ) : (
          <div className="space-y-4">
            {sessions.map((s) => (
              <div
                key={s.id}
                className="bg-[#111114] border border-[#2A2A30] hover:border-[#FFD700]/40 rounded-2xl p-6 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-5"
              >
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-[#17171B] border border-[#2A2A30] text-[#FFD700] flex items-center justify-center shrink-0">
                    <BookOpen className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <span className="text-xs font-bold text-[#FFD700]">{s.division_name}</span>
                      <span className="text-[#2A2A30]">&bull;</span>
                      <span className="text-xs text-[#A1A1AA] flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" />
                        {s.lecture_date}
                      </span>
                      <span className="text-[#2A2A30]">&bull;</span>
                      <span className="text-xs text-[#A1A1AA] flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {s.start_time}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-[#F5F5F5]">{s.subject}: {s.title}</h3>
                    <div className="flex items-center gap-3 mt-2 text-xs">
                      <span className="text-[#7BD88F]">Present: {s.present_count}</span>
                      <span className="text-red-400">Absent: {s.absent_count}</span>
                      {s.flagged_count > 0 && (
                        <span className="text-[#FFD700]">Flagged: {s.flagged_count}</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full md:w-auto justify-end">
                  <StatusBadge status={s.status} />
                  <Link
                    href={`/teacher/lectures/${s.id}`}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#17171B] hover:bg-[#1F1F24] border border-[#2A2A30] text-xs font-semibold text-[#F5F5F5] transition-colors"
                  >
                    <span>View Register</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </DashboardLayout>
    </ProtectedPage>
  );
}
