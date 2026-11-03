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
  BookOpen,
  PlusCircle,
  Calendar,
  Clock,
  ArrowRight,
  RefreshCw,
  AlertCircle
} from "lucide-react";

export default function TeacherLecturesListPage() {
  const { user } = useAuth();
  const [lectures, setLectures] = useState<LectureSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filterDate, setFilterDate] = useState("");

  async function loadLectures() {
    setLoading(true);
    setError(null);
    try {
      const data = await lectureService.getAll({
        teacher_id: user?.id,
        date: filterDate || undefined,
      });
      setLectures(data);
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
    if (!user) return;
    loadLectures();
  }, [filterDate, user]);

  return (
    <ProtectedPage requiredRole="teacher">
      <DashboardLayout
        role="teacher"
        title="Lecture Sessions Register"
        subtitle="Manage and review classroom attendance verification sessions."
        breadcrumbs={[{ label: "Lectures" }]}
        actions={
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={loadLectures}
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
        {/* Date Filter Bar */}
        <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-4 mb-6 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs">
            <Calendar className="w-4 h-4 text-[#FFD700]" />
            <input
              type="date"
              value={filterDate}
              onChange={(e) => setFilterDate(e.target.value)}
              className="h-10 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
            />
            {filterDate && (
              <button
                type="button"
                onClick={() => setFilterDate("")}
                className="text-xs text-[#A1A1AA] hover:text-[#F5F5F5] ml-2"
              >
                Clear Filter
              </button>
            )}
          </div>
          <span className="text-xs text-[#A1A1AA]">
            Total sessions: <strong className="text-[#F5F5F5]">{lectures.length}</strong>
          </span>
        </div>

        {/* Lectures List */}
        {loading ? (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-12 text-center text-xs text-[#A1A1AA]">
            <RefreshCw className="w-5 h-5 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Loading lecture sessions from FastAPI...</span>
          </div>
        ) : error ? (
          <EmptyState
            icon={AlertCircle}
            title="Database Connection Notice"
            description={`${error} No mock sessions are displayed.`}
            action={
              <button
                type="button"
                onClick={loadLectures}
                className="px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
              >
                Retry
              </button>
            }
          />
        ) : lectures.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No Lecture Sessions Found"
            description="No lecture attendance sessions match the selected criteria. Click 'Create Lecture' to establish a new session."
            action={
              <Link
                href="/teacher/lectures/new"
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
              >
                <PlusCircle className="w-4 h-4" />
                <span>Create New Lecture</span>
              </Link>
            }
          />
        ) : (
          <div className="space-y-4">
            {lectures.map((lec) => (
              <div
                key={lec.id}
                className="bg-[#111114] border border-[#2A2A30] hover:border-[#FFD700]/40 rounded-2xl p-6 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-5"
              >
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-[#17171B] border border-[#2A2A30] text-[#FFD700] flex items-center justify-center shrink-0">
                    <BookOpen className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <span className="text-xs font-bold text-[#FFD700]">{lec.division_name}</span>
                      <span className="text-[#2A2A30]">&bull;</span>
                      <span className="text-xs text-[#A1A1AA] flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" />
                        {lec.lecture_date}
                      </span>
                      <span className="text-[#2A2A30]">&bull;</span>
                      <span className="text-xs text-[#A1A1AA] flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {lec.start_time}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-[#F5F5F5]">{lec.subject}: {lec.title}</h3>
                    <p className="text-xs text-[#A1A1AA] mt-1">
                      Enrolled: <strong className="text-[#F5F5F5]">{lec.total_enrolled}</strong> &bull; Present: <strong className="text-[#7BD88F]">{lec.present_count}</strong> &bull; Absent: <strong className="text-red-400">{lec.absent_count}</strong> &bull; Flagged: <strong className="text-[#FFD700]">{lec.flagged_count}</strong>
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full md:w-auto justify-end">
                  <StatusBadge status={lec.status} />

                  {lec.status === "finalized" ? (
                    <Link
                      href={`/teacher/lectures/${lec.id}`}
                      className="px-4 py-2 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors"
                    >
                      View Record
                    </Link>
                  ) : (
                    <Link
                      href={`/teacher/lectures/${lec.id}/review`}
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md transition-all"
                    >
                      <span>Review Attendance</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </DashboardLayout>
    </ProtectedPage>
  );
}
