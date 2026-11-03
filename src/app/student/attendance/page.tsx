"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { useAuth } from "@/context/AuthContext";
import { statsService } from "@/lib/services";
import {
  Calendar,
  Search,
  RefreshCw
} from "lucide-react";

export default function StudentAttendanceHistoryPage() {
  const { user } = useAuth();
  const [records, setRecords] = useState<
    Array<{
      date: string;
      subject: string;
      status: "PRESENT" | "ABSENT" | "FLAGGED";
      teacher_name: string;
    }>
  >([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    if (!user) return;
    statsService
      .getStudentStats(user.id)
      .then((res) => {
        setRecords(res.recent_records || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  const filtered = records.filter((r) => {
    const matchesSearch = r.subject.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || r.status.toLowerCase() === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <ProtectedPage requiredRole="student">
      <DashboardLayout
        role="student"
        title="My Attendance Ledger"
        subtitle="Chronological record of verified lecture attendances published by faculty."
        breadcrumbs={[{ label: "Attendance History" }]}
      >
        <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-4 mb-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-[#A1A1AA] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by course subject..."
              className="w-full h-10 pl-10 pr-4 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/50 focus:border-[#FFD700] focus:outline-none transition-colors"
            />
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none transition-colors"
            >
              <option value="all">All Statuses</option>
              <option value="present">Present Only</option>
              <option value="absent">Absent Only</option>
              <option value="flagged">Flagged</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-12 text-center text-xs text-[#A1A1AA]">
            <RefreshCw className="w-5 h-5 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Retrieving attendance history...</span>
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={Calendar}
            title="No Attendance Records Found"
            description="No lecture records match your selected search or filter criteria."
          />
        ) : (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-[#17171B] text-[#A1A1AA] border-b border-[#2A2A30]">
                    <th className="py-3.5 px-4 font-semibold">Date</th>
                    <th className="py-3.5 px-4 font-semibold">Subject Course</th>
                    <th className="py-3.5 px-4 font-semibold">Faculty In-Charge</th>
                    <th className="py-3.5 px-4 font-semibold">Attendance Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2A2A30]/50 text-[#F5F5F5]">
                  {filtered.map((r, i) => (
                    <tr key={i} className="hover:bg-[#17171B]/50 transition-colors">
                      <td className="py-3.5 px-4 text-[#A1A1AA] font-mono">{r.date}</td>
                      <td className="py-3.5 px-4 font-bold text-[#F5F5F5]">{r.subject}</td>
                      <td className="py-3.5 px-4 text-[#A1A1AA]">{r.teacher_name}</td>
                      <td className="py-3.5 px-4">
                        <StatusBadge status={r.status.toLowerCase()} />
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
