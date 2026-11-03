"use client";

import React, { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import {
  Settings,
  Shield,
  Save,
  CheckCircle2,
  ScanFace,
  Building
} from "lucide-react";

export default function AdminSettingsPage() {
  const [institutionName, setInstitutionName] = useState("College of Engineering & Technology");
  const [campusCode, setCampusCode] = useState("COET-CAMPUS-01");
  const [cutoffThreshold, setCutoffThreshold] = useState("75");
  const [aiConfidenceThreshold, setAiConfidenceThreshold] = useState("85");
  const [rfidDailyWindow, setRfidDailyWindow] = useState("08:00 - 11:00");
  const [saved, setSaved] = useState(false);

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  return (
    <ProtectedPage requiredRole="admin">
      <DashboardLayout
        role="admin"
        title="Institutional System Settings"
        subtitle="Manage campus policies, biometric thresholds, and RFID gateway authorization keys."
        breadcrumbs={[{ label: "Settings" }]}
      >
        {saved && (
          <div className="mb-6 p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/60 text-[#7BD88F] text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>Institutional configuration preferences updated successfully.</span>
          </div>
        )}

        <form onSubmit={handleSave} className="max-w-4xl space-y-6">
          {/* Institution Identity */}
          <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7">
            <div className="flex items-center gap-2.5 text-xs font-bold text-[#FFD700] mb-2">
              <Building className="w-4 h-4" />
              <span>CAMPUS PROFILE</span>
            </div>
            <h3 className="text-base font-bold text-[#F5F5F5] mb-5">Institutional Identity</h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Institution Name</label>
                <input
                  type="text"
                  required
                  value={institutionName}
                  onChange={(e) => setInstitutionName(e.target.value)}
                  className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Campus Code</label>
                <input
                  type="text"
                  required
                  value={campusCode}
                  onChange={(e) => setCampusCode(e.target.value)}
                  className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] font-mono focus:border-[#FFD700] focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Attendance Policy & Cutoff Threshold */}
          <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7">
            <div className="flex items-center gap-2.5 text-xs font-bold text-[#FFD700] mb-2">
              <Shield className="w-4 h-4" />
              <span>STATUTORY POLICIES</span>
            </div>
            <h3 className="text-base font-bold text-[#F5F5F5] mb-5">Attendance Rules & Thresholds</h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                  Statutory Attendance Cutoff (%)
                </label>
                <input
                  type="number"
                  min="50"
                  max="100"
                  required
                  value={cutoffThreshold}
                  onChange={(e) => setCutoffThreshold(e.target.value)}
                  className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                />
                <span className="text-[11px] text-[#A1A1AA] mt-1 block">
                  Students below this percentage are automatically flagged in defaulter reports.
                </span>
              </div>

              <div>
                <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                  RFID Daily Gate Check-In Window
                </label>
                <input
                  type="text"
                  required
                  value={rfidDailyWindow}
                  onChange={(e) => setRfidDailyWindow(e.target.value)}
                  className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                />
                <span className="text-[11px] text-[#A1A1AA] mt-1 block">
                  Daily presence scans are strictly recorded once per day per student.
                </span>
              </div>
            </div>
          </div>

          {/* AI Face Verification Parameters */}
          <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7">
            <div className="flex items-center gap-2.5 text-xs font-bold text-[#FFD700] mb-2">
              <ScanFace className="w-4 h-4" />
              <span>AI VISION PARAMETERS</span>
            </div>
            <h3 className="text-base font-bold text-[#F5F5F5] mb-5">Face Verification Sensitivity</h3>

            <div className="max-w-md">
              <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                AI Match Confidence Threshold ({aiConfidenceThreshold}%)
              </label>
              <input
                type="range"
                min="60"
                max="95"
                value={aiConfidenceThreshold}
                onChange={(e) => setAiConfidenceThreshold(e.target.value)}
                className="w-full accent-[#FFD700]"
              />
              <div className="flex justify-between text-[11px] text-[#A1A1AA] mt-1">
                <span>Relaxed (60%)</span>
                <span>Balanced (85%)</span>
                <span>Strict (95%)</span>
              </div>
              <p className="text-[11px] text-[#A1A1AA] mt-2">
                Detections falling below this threshold are marked as <strong>FLAGGED</strong> and routed to the faculty review screen.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-end">
            <button
              type="submit"
              className="inline-flex items-center gap-2 px-7 py-3 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs tracking-wider shadow-[0_0_20px_rgba(255,215,0,0.25)] transition-all"
            >
              <Save className="w-4 h-4" />
              <span>Save System Settings</span>
            </button>
          </div>
        </form>
      </DashboardLayout>
    </ProtectedPage>
  );
}
