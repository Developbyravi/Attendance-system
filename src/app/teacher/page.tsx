"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import StatCard from "@/components/StatCard";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { useAuth } from "@/context/AuthContext";
import { lectureService, checkInService, LectureSession } from "@/lib/services";

import {
  BookOpen,
  UserCheck,
  AlertTriangle,
  PlusCircle,
  Clock,
  ArrowRight,
  RefreshCw,
  Users,
  Camera,
  Calendar,
  AlertCircle
} from "lucide-react";

export default function TeacherDashboardPage() {
  const { user } = useAuth();
  const [lectures, setLectures] = useState<LectureSession[]>([]);
  const [todayCheckinsCount, setTodayCheckinsCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const todayStr = new Date().toISOString().split("T")[0];

  async function loadTeacherData() {
    setLoading(true);
    setError(null);
    try {
      const [lectureList, checkins] = await Promise.allSettled([
        lectureService.getAll({ teacher_id: user?.id, date: todayStr }),
        checkInService.getToday(),
      ]);

      if (lectureList.status === "fulfilled") {
        setLectures(lectureList.value);
      } else {
        setError("Unable to connect to FastAPI /lectures endpoint.");
      }

      if (checkins.status === "fulfilled") {
        setTodayCheckinsCount(checkins.value.length);
      }
    } catch {
      setError("Failed to load lecture registers. Backend service may be offline.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!user) return;
    loadTeacherData();
  }, [user]);

  // Derived metrics from real data
  const totalLecturesToday = lectures.length;
  const pendingReviews = lectures.filter((l) => l.status === "review_pending" || l.status === "in_progress").length;
  const flaggedCount = lectures.reduce((acc, curr) => acc + (curr.flagged_count || 0), 0);

  return (
    <ProtectedPage requiredRole="teacher">
      <DashboardLayout
        role="teacher"
        title={`Welcome, ${user?.full_name || "Faculty Member"}`}
        subtitle="Manage assigned division registers, conduct AI classroom verification, and review student attendance."
        actions={
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={loadTeacherData}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-[#FFD700]" : ""}`} />
              <span>Refresh</span>
            </button>
            <Link
              href="/teacher/lectures/new"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-[0_0_15px_rgba(255,215,0,0.2)] transition-all"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Create Lecture</span>
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
                {error} — All metrics and lectures are displayed strictly from verified database records.
              </p>
            </div>
          </div>
        )}

        {/* 4 Faculty Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            label="Today's Sessions"
            value={totalLecturesToday}
            subtext="Assigned lecture slots"
            icon={BookOpen}
          />
          <StatCard
            label="Daily Campus Gate Taps"
            value={todayCheckinsCount}
            subtext="RFID student arrivals"
            icon={UserCheck}
          />
          <StatCard
            label="Pending Reviews"
            value={pendingReviews}
            subtext="Lectures awaiting finalization"
            icon={Clock}
          />
          <StatCard
            label="Flagged Discrepancies"
            value={flaggedCount}
            subtext="Requires faculty authority"
            icon={AlertTriangle}
          />
        </div>

        {/* Quick Actions Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          <Link
            href="/teacher/lectures/new"
            className="p-4 rounded-2xl bg-[#111114] border border-[#2A2A30] hover:border-[#FFD700]/50 transition-all flex items-center gap-3 text-xs font-bold text-[#F5F5F5] group"
          >
            <div className="w-9 h-9 rounded-xl bg-[#17171B] border border-[#2A2A30] text-[#FFD700] flex items-center justify-center group-hover:border-[#FFD700]/40 transition-colors">
              <PlusCircle className="w-4 h-4" />
            </div>
            <span>Create Lecture</span>
          </Link>

          <Link
            href="/teacher/daily-checkins"
            className="p-4 rounded-2xl bg-[#111114] border border-[#2A2A30] hover:border-[#FFD700]/50 transition-all flex items-center gap-3 text-xs font-bold text-[#F5F5F5] group"
          >
            <div className="w-9 h-9 rounded-xl bg-[#17171B] border border-[#2A2A30] text-[#FFD700] flex items-center justify-center group-hover:border-[#FFD700]/40 transition-colors">
              <UserCheck className="w-4 h-4" />
            </div>
            <span>Daily RFID Taps</span>
          </Link>

          <Link
            href="/teacher/students"
            className="p-4 rounded-2xl bg-[#111114] border border-[#2A2A30] hover:border-[#FFD700]/50 transition-all flex items-center gap-3 text-xs font-bold text-[#F5F5F5] group"
          >
            <div className="w-9 h-9 rounded-xl bg-[#17171B] border border-[#2A2A30] text-[#FFD700] flex items-center justify-center group-hover:border-[#FFD700]/40 transition-colors">
              <Users className="w-4 h-4" />
            </div>
            <span>My Students</span>
          </Link>

          <Link
            href="/teacher/reports"
            className="p-4 rounded-2xl bg-[#111114] border border-[#2A2A30] hover:border-[#FFD700]/50 transition-all flex items-center gap-3 text-xs font-bold text-[#F5F5F5] group"
          >
            <div className="w-9 h-9 rounded-xl bg-[#17171B] border border-[#2A2A30] text-[#FFD700] flex items-center justify-center group-hover:border-[#FFD700]/40 transition-colors">
              <Calendar className="w-4 h-4" />
            </div>
            <span>Class Ledgers</span>
          </Link>
        </div>

        {/* Today's Lectures Table */}
        <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7 shadow-xl mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                TODAY&apos;S SCHEDULE
              </span>
              <h3 className="text-lg font-bold text-[#F5F5F5]">Active Lecture Sessions</h3>
            </div>
            <Link
              href="/teacher/lectures"
              className="text-xs text-[#FFD700] hover:text-[#FFE34D] flex items-center gap-1 font-semibold"
            >
              <span>View All Sessions</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {loading ? (
            <div className="py-12 text-center text-xs text-[#A1A1AA]">
              <RefreshCw className="w-5 h-5 animate-spin text-[#FFD700] mx-auto mb-2" />
              <span>Checking scheduled lecture sessions...</span>
            </div>
          ) : lectures.length === 0 ? (
            <EmptyState
              icon={BookOpen}
              title="No Lectures Scheduled Today"
              description="You have no active lecture sessions logged for today. Click 'Create Lecture' to schedule a classroom verification session."
              action={
                <Link
                  href="/teacher/lectures/new"
                  className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>Start New Lecture</span>
                </Link>
              }
            />
          ) : (
            <div className="space-y-4">
              {lectures.map((lec) => (
                <div
                  key={lec.id}
                  className="bg-[#17171B] border border-[#2A2A30] hover:border-[#FFD700]/40 rounded-2xl p-5 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
                >
                  <div className="flex items-start gap-3.5">
                    <div className="w-11 h-11 rounded-xl bg-[#111114] border border-[#2A2A30] text-[#FFD700] flex items-center justify-center shrink-0">
                      <BookOpen className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-bold text-[#FFD700]">{lec.division_name}</span>
                        <span className="text-[#2A2A30]">&bull;</span>
                        <span className="text-xs text-[#A1A1AA] flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          {lec.start_time}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-[#F5F5F5]">{lec.subject} — {lec.title}</h4>
                      <p className="text-xs text-[#A1A1AA] mt-1">
                        Enrolled: {lec.total_enrolled} | Present: {lec.present_count} | Flagged: {lec.flagged_count}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 w-full md:w-auto justify-end">
                    <StatusBadge status={lec.status} />

                    {lec.status === "finalized" ? (
                      <Link
                        href={`/teacher/lectures/${lec.id}`}
                        className="px-4 py-2 rounded-xl bg-[#111114] border border-[#2A2A30] text-xs font-semibold text-[#F5F5F5] hover:text-[#FFD700] transition-colors"
                      >
                        View Locked Record
                      </Link>
                    ) : lec.status === "review_pending" ? (
                      <Link
                        href={`/teacher/lectures/${lec.id}/review`}
                        className="px-4 py-2 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md transition-all flex items-center gap-1.5"
                      >
                        <span>Review Attendance</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    ) : (
                      <Link
                        href={`/teacher/lectures/${lec.id}`}
                        className="px-4 py-2 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md transition-all flex items-center gap-1.5"
                      >
                        <Camera className="w-3.5 h-3.5" />
                        <span>Upload Photo</span>
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedPage>
  );
}
