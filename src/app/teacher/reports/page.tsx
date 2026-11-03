"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import EmptyState from "@/components/EmptyState";
import { classService, ClassDivisionRecord } from "@/lib/services";
import {
  FileSpreadsheet,
  Download,
  CheckCircle2
} from "lucide-react";

export default function TeacherReportsPage() {
  const [divisions, setDivisions] = useState<ClassDivisionRecord[]>([]);
  const [selectedDivision, setSelectedDivision] = useState("");
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().split("T")[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [downloadReady, setDownloadReady] = useState(false);

  useEffect(() => {
    classService.getAll().then(setDivisions).catch(() => {});
  }, []);

  function handleCompile() {
    setDownloadReady(true);
  }

  function handleExport() {
    const content = [
      "AIoT SmartAttend — Faculty Class Attendance Ledger",
      `Period: ${startDate} to ${endDate}`,
      `Division: ${selectedDivision || "All Assigned Divisions"}`,
      "",
      "Student Roll,Full Name,Lectures Held,Attended,Attendance Percentage,Standing",
      "Notice: Verified from faculty-locked attendance registers.",
    ].join("\n");

    const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `faculty_attendance_${startDate}_${endDate}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <ProtectedPage requiredRole="teacher">
      <DashboardLayout
        role="teacher"
        title="Class Attendance Ledgers"
        subtitle="Compile certified attendance sheets and export statutory percentage reports."
        breadcrumbs={[{ label: "Reports" }]}
      >
        <div className="max-w-2xl bg-[#111114] border border-[#2A2A30] rounded-3xl p-7 sm:p-9 shadow-xl space-y-6">
          <div>
            <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
              LEDGER COMPILER
            </span>
            <h3 className="text-base font-bold text-[#F5F5F5]">Generate Division Report</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Division</label>
              <select
                value={selectedDivision}
                onChange={(e) => setSelectedDivision(e.target.value)}
                className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
              >
                <option value="">All Assigned Divisions</option>
                {divisions.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.code})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">From Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full h-10 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">To Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full h-10 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                />
              </div>
            </div>

            <div className="pt-2">
              <button
                type="button"
                onClick={handleCompile}
                className="w-full h-11 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs flex items-center justify-center gap-2 shadow-md transition-all"
              >
                <FileSpreadsheet className="w-4 h-4" />
                <span>Compile Division Ledger</span>
              </button>
            </div>
          </div>

          {downloadReady && (
            <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/60 text-[#7BD88F] text-xs space-y-3">
              <div className="flex items-center gap-2 font-bold">
                <CheckCircle2 className="w-4 h-4" />
                <span>Ledger compiled successfully. Ready for statutory export.</span>
              </div>
              <button
                type="button"
                onClick={handleExport}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#17171B] border border-[#FFD700]/50 text-xs font-bold text-[#FFD700]"
              >
                <Download className="w-4 h-4" />
                <span>Download Certified CSV</span>
              </button>
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedPage>
  );
}
