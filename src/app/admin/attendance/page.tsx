"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { checkInService, classService, DailyCheckInRecord, ClassDivisionRecord } from "@/lib/services";

import {
  UserCheck,
  Search,
  Download,
  Calendar,
  RefreshCw,
  AlertCircle,
  Clock
} from "lucide-react";

export default function AdminAttendancePage() {
  const [logs, setLogs] = useState<DailyCheckInRecord[]>([]);
  const [divisions, setDivisions] = useState<ClassDivisionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDivision, setSelectedDivision] = useState("");
  const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().split("T")[0]);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [checkins, classList] = await Promise.allSettled([
        checkInService.getToday({ division_id: selectedDivision || undefined, date: selectedDate }),
        classService.getAll(),
      ]);

      if (checkins.status === "fulfilled") {
        setLogs(checkins.value);
      } else {
        setError("Unable to connect to FastAPI /daily-checkins endpoint.");
      }

      if (classList.status === "fulfilled") {
        setDivisions(classList.value);
      }
    } catch {
      setError("Failed to fetch check-in logs from backend.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [selectedDivision, selectedDate]);

  function exportCSV() {
    if (logs.length === 0) {
      alert("No attendance logs available to export for this date.");
      return;
    }
    const headers = ["ID", "Student Name", "Roll Number", "Division", "RFID UID", "Device ID", "Check-in Time", "Verified"];
    const rows = logs.map((l) => [
      l.id,
      `"${l.student_name}"`,
      l.roll_number,
      l.division_name || "",
      l.rfid_uid,
      l.device_id,
      l.check_in_time,
      l.is_verified ? "Yes" : "No",
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `smartattend_campus_logs_${selectedDate}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  const filtered = logs.filter((l) => {
    const q = searchQuery.toLowerCase();
    return (
      l.student_name?.toLowerCase().includes(q) ||
      l.roll_number?.toLowerCase().includes(q) ||
      l.rfid_uid?.toLowerCase().includes(q)
    );
  });

  return (
    <ProtectedPage requiredRole="admin">
      <DashboardLayout
        role="admin"
        title="Campus Attendance Ledger"
        subtitle="Institution-wide daily RFID gate taps and synchronized check-in timestamps."
        breadcrumbs={[{ label: "Attendance" }]}
        actions={
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={exportCSV}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#17171B] hover:bg-[#1F1F24] border border-[#2A2A30] text-xs font-semibold text-[#F5F5F5] transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Ledger CSV</span>
            </button>
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
        {/* Filters Toolbar */}
        <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-4 mb-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:w-80">
            <Search className="w-4 h-4 text-[#A1A1AA] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by student or roll number..."
              className="w-full h-10 pl-10 pr-4 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/50 focus:border-[#FFD700] focus:outline-none transition-colors"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-[#FFD700]" />
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="h-10 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
              />
            </div>

            <select
              value={selectedDivision}
              onChange={(e) => setSelectedDivision(e.target.value)}
              className="h-10 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
            >
              <option value="">All Divisions</option>
              {divisions.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Attendance Records Table */}
        {loading ? (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-12 text-center text-xs text-[#A1A1AA]">
            <RefreshCw className="w-6 h-6 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Querying verified daily check-in events...</span>
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
            title="No Attendance Events Logged"
            description={`No RFID card taps have been recorded for ${selectedDate}. When students scan badges at physical gates, check-in timestamps will appear here automatically.`}
          />
        ) : (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-[#17171B] text-[#A1A1AA] border-b border-[#2A2A30]">
                    <th className="py-3.5 px-4 font-semibold">Student Name</th>
                    <th className="py-3.5 px-4 font-semibold">Roll Number</th>
                    <th className="py-3.5 px-4 font-semibold">Division</th>
                    <th className="py-3.5 px-4 font-semibold">RFID Card UID</th>
                    <th className="py-3.5 px-4 font-semibold">Gate Terminal</th>
                    <th className="py-3.5 px-4 font-semibold">Check-in Time</th>
                    <th className="py-3.5 px-4 font-semibold">Verification Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2A2A30]/50 text-[#F5F5F5]">
                  {filtered.map((log) => (
                    <tr key={log.id} className="hover:bg-[#17171B]/50 transition-colors">
                      <td className="py-3.5 px-4 font-bold text-[#F5F5F5]">{log.student_name}</td>
                      <td className="py-3.5 px-4 text-[#FFD700] font-semibold">{log.roll_number}</td>
                      <td className="py-3.5 px-4">{log.division_name || "—"}</td>
                      <td className="py-3.5 px-4 font-mono text-[11px] text-[#A1A1AA]">{log.rfid_uid}</td>
                      <td className="py-3.5 px-4 text-xs font-mono">{log.device_id}</td>
                      <td className="py-3.5 px-4 text-[#A1A1AA] flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-[#FFD700]" />
                        <span>{log.check_in_time}</span>
                      </td>
                      <td className="py-3.5 px-4">
                        <StatusBadge
                          status={log.is_verified ? "verified" : "pending"}
                          labelOverride={log.is_verified ? "Verified Daily Tap" : "Unverified"}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-4 border-t border-[#2A2A30] flex items-center justify-between text-[11px] text-[#A1A1AA]">
              <span>Showing {filtered.length} daily card scans</span>
              <span>FastAPI /daily-checkins live feed</span>
            </div>
          </div>
        )}
      </DashboardLayout>
    </ProtectedPage>
  );
}
