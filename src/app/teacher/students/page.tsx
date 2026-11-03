"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { studentService, classService, StudentRecord, ClassDivisionRecord } from "@/lib/services";

import {
  GraduationCap,
  Search,
  RefreshCw,
  AlertCircle
} from "lucide-react";

export default function TeacherStudentsPage() {
  const [students, setStudents] = useState<StudentRecord[]>([]);
  const [divisions, setDivisions] = useState<ClassDivisionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDivision, setSelectedDivision] = useState("");

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [stuData, classData] = await Promise.allSettled([
        studentService.getAll({ query: searchQuery || undefined, division_id: selectedDivision || undefined }),
        classService.getAll(),
      ]);

      if (stuData.status === "fulfilled") {
        setStudents(stuData.value);
      } else {
        setError("Unable to connect to FastAPI /students endpoint.");
      }

      if (classData.status === "fulfilled") {
        setDivisions(classData.value);
      }
    } catch {
      setError("Failed to fetch assigned students.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [selectedDivision]);

  const filtered = students.filter((s) => {
    const q = searchQuery.toLowerCase();
    return (
      s.full_name?.toLowerCase().includes(q) ||
      s.roll_number?.toLowerCase().includes(q)
    );
  });

  return (
    <ProtectedPage requiredRole="teacher">
      <DashboardLayout
        role="teacher"
        title="Assigned Students Directory"
        subtitle="Roster of enrolled students in your assigned classroom divisions."
        breadcrumbs={[{ label: "Assigned Students" }]}
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

          <select
            value={selectedDivision}
            onChange={(e) => setSelectedDivision(e.target.value)}
            className="h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
          >
            <option value="">All Assigned Divisions</option>
            {divisions.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.code})
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-12 text-center text-xs text-[#A1A1AA]">
            <RefreshCw className="w-5 h-5 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Loading assigned student directory...</span>
          </div>
        ) : error ? (
          <EmptyState
            icon={AlertCircle}
            title="Database Connection Notice"
            description={`${error} No simulated records are presented.`}
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
            icon={GraduationCap}
            title="No Enrolled Students"
            description="No active students were returned for this division filter."
          />
        ) : (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-[#17171B] text-[#A1A1AA] border-b border-[#2A2A30]">
                    <th className="py-3.5 px-4 font-semibold">Roll No</th>
                    <th className="py-3.5 px-4 font-semibold">Student Name</th>
                    <th className="py-3.5 px-4 font-semibold">Email</th>
                    <th className="py-3.5 px-4 font-semibold">Division</th>
                    <th className="py-3.5 px-4 font-semibold">RFID Tag</th>
                    <th className="py-3.5 px-4 font-semibold">Enrolled Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2A2A30]/50 text-[#F5F5F5]">
                  {filtered.map((s) => (
                    <tr key={s.id} className="hover:bg-[#17171B]/50 transition-colors">
                      <td className="py-3.5 px-4 font-bold text-[#FFD700]">{s.roll_number}</td>
                      <td className="py-3.5 px-4 font-medium">{s.full_name}</td>
                      <td className="py-3.5 px-4 text-[#A1A1AA]">{s.email}</td>
                      <td className="py-3.5 px-4">{s.division_name || "—"}</td>
                      <td className="py-3.5 px-4 font-mono text-[11px] text-[#A1A1AA]">
                        {s.rfid_uid || <span className="text-zinc-600 italic">Unpaired</span>}
                      </td>
                      <td className="py-3.5 px-4">
                        <StatusBadge
                          status={s.is_active ? "verified" : "offline"}
                          labelOverride={s.is_active ? "Active" : "Inactive"}
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
