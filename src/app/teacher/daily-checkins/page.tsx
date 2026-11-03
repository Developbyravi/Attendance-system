"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { checkInService, DailyCheckInRecord } from "@/lib/services";
import { ApiError } from "@/lib/api";
import {
  UserCheck,
  Search,
  Calendar,
  Clock,
  RefreshCw,
  AlertCircle
} from "lucide-react";

export default function TeacherDailyCheckinsPage() {
  const [logs, setLogs] = useState<DailyCheckInRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().split("T")[0]);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const data = await checkInService.getToday({ date: selectedDate });
      setLogs(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to connect to FastAPI /daily-checkins endpoint.");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [selectedDate]);

  const filtered = logs.filter((l) => {
    const q = searchQuery.toLowerCase();
    return (
      l.student_name?.toLowerCase().includes(q) ||
      l.roll_number?.toLowerCase().includes(q) ||
      l.division_name?.toLowerCase().includes(q)
    );
  });

  return (
    <ProtectedPage requiredRole="teacher">
      <DashboardLayout
        role="teacher"
        title="Daily RFID Gate Check-Ins"
        subtitle="Monitor students' morning campus arrivals scanned through physical RC522 reader gates."
        breadcrumbs={[{ label: "Daily Check-Ins" }]}
        actions={
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={loadData}
              disabled={loading}
              className="p-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-[#FFD700]" : ""}`} />
            </button>
          </div>
        }
      >
        <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-4 mb-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-[#A1A1AA] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by student name or roll..."
              className="w-full h-10 pl-10 pr-4 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/50 focus:border-[#FFD700] focus:outline-none transition-colors"
            />
          </div>

          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-[#FFD700]" />
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="h-10 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
            />
          </div>
        </div>

        {loading ? (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-12 text-center text-xs text-[#A1A1AA]">
            <RefreshCw className="w-6 h-6 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Retrieving gate check-in logs...</span>
          </div>
        ) : error ? (
          <EmptyState
            icon={AlertCircle}
            title="Database Connection Notice"
            description={`${error} No simulated check-in records are shown.`}
            action={
              <button
                type="button"
                onClick={loadData}
                className="px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
              >
                Retry
              </button>
            }
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={UserCheck}
            title="No Daily Check-Ins Recorded"
            description={`No student RFID scans recorded for ${selectedDate}. Daily gate presence will populate automatically as cards are tapped.`}
          />
        ) : (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-[#17171B] text-[#A1A1AA] border-b border-[#2A2A30]">
                    <th className="py-3.5 px-4 font-semibold">Roll No</th>
                    <th className="py-3.5 px-4 font-semibold">Student Name</th>
                    <th className="py-3.5 px-4 font-semibold">Division</th>
                    <th className="py-3.5 px-4 font-semibold">Gate Location</th>
                    <th className="py-3.5 px-4 font-semibold">Check-In Time</th>
                    <th className="py-3.5 px-4 font-semibold">Daily Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2A2A30]/50 text-[#F5F5F5]">
                  {filtered.map((log) => (
                    <tr key={log.id} className="hover:bg-[#17171B]/50 transition-colors">
                      <td className="py-3.5 px-4 font-bold text-[#FFD700]">{log.roll_number}</td>
                      <td className="py-3.5 px-4 font-medium">{log.student_name}</td>
                      <td className="py-3.5 px-4">{log.division_name || "—"}</td>
                      <td className="py-3.5 px-4 font-mono text-xs">{log.device_id}</td>
                      <td className="py-3.5 px-4 text-[#A1A1AA] flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-[#FFD700]" />
                        <span>{log.check_in_time}</span>
                      </td>
                      <td className="py-3.5 px-4">
                        <StatusBadge
                          status="verified"
                          labelOverride="Campus Present"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </DashboardLayout>
    </ProtectedPage>
  );
}
