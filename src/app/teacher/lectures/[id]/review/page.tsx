"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { lectureService, LectureSession, AttendanceReviewItem } from "@/lib/services";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import {
  ShieldCheck,
  CheckCircle2,
  Lock,
  RefreshCw,
  AlertCircle,
  Radio,
  ScanFace,
  X,
  Loader2,
  Eye,
  EyeOff,
  Camera
} from "lucide-react";

export default function AttendanceReviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const { user } = useAuth();
  const lectureId = resolvedParams.id;

  const [lecture, setLecture] = useState<LectureSession | null>(null);
  const [roster, setRoster] = useState<AttendanceReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tab filter
  const [activeTab, setActiveTab] = useState<"all" | "flagged" | "present" | "absent" | "pending">("all");

  // Visual overlay display mode: "overlay" | "clean" | "hidden"
  const [overlayMode, setOverlayMode] = useState<"overlay" | "clean" | "hidden">("overlay");

  // Finalization state & confirmation modal
  const [showFinalizeModal, setShowFinalizeModal] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function loadReviewData() {
    setLoading(true);
    setError(null);
    try {
      const [lecData, rosterData] = await Promise.allSettled([
        lectureService.getById(lectureId),
        lectureService.getReviewRoster(lectureId),
      ]);

      if (lecData.status === "fulfilled") {
        setLecture(lecData.value);
      } else {
        setError("Unable to connect to FastAPI /lectures/:id endpoint.");
      }

      if (rosterData.status === "fulfilled") {
        setRoster(rosterData.value);
      } else {
        setError("Unable to connect to FastAPI /lectures/:id/review roster endpoint.");
      }
    } catch {
      setError("Failed to fetch lecture roster from server.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!user) return;
    loadReviewData();
  }, [lectureId, user]);

  const isFinalized = lecture?.status === "finalized";

  async function handleUpdateStudentStatus(
    studentId: string | number,
    status: "PRESENT" | "ABSENT" | "FLAGGED"
  ) {
    if (isFinalized) return;

    try {
      await lectureService.updateStudentAttendance(lectureId, studentId, status);
      // Locally update roster state
      setRoster((prev) =>
        prev.map((item) =>
          item.student_id === studentId
            ? { ...item, attendance_status: status, verification_source: "TEACHER_MANUAL" }
            : item
        )
      );
    } catch (err: unknown) {
      alert(err instanceof ApiError ? err.message : "Failed to update attendance status.");
    }
  }

  async function handleFinalizeRegister() {
    if (finalizing) return;
    setFinalizing(true);
    try {
      await lectureService.finalizeAttendance(lectureId);
      setShowFinalizeModal(false);
      setSuccessMessage("Lecture attendance finalized and permanently locked.");
      loadReviewData();
    } catch (err: unknown) {
      alert(err instanceof ApiError ? err.message : "Failed to finalize attendance with FastAPI.");
    } finally {
      setFinalizing(false);
    }
  }

  const flaggedCount = roster.filter((r) => r.attendance_status === "FLAGGED").length;
  const presentCount = roster.filter((r) => r.attendance_status === "PRESENT").length;
  const absentCount = roster.filter((r) => r.attendance_status === "ABSENT").length;
  const pendingCount = roster.filter((r) => r.attendance_status === "PENDING").length;

  const filteredRoster = roster.filter((item) => {
    if (activeTab === "flagged") return item.attendance_status === "FLAGGED";
    if (activeTab === "present") return item.attendance_status === "PRESENT";
    if (activeTab === "absent") return item.attendance_status === "ABSENT";
    if (activeTab === "pending") return item.attendance_status === "PENDING";
    return true;
  });

  const hasPhoto = Boolean(lecture?.classroom_photo_url || lecture?.overlay_image_url);
  const currentPhotoSrc =
    overlayMode === "overlay"
      ? (lecture?.overlay_image_url || lecture?.classroom_photo_url)
      : (lecture?.classroom_photo_url || lecture?.overlay_image_url);

  return (
    <ProtectedPage requiredRole="teacher">
      <DashboardLayout
        role="teacher"
        title="Attendance Verification Review"
        subtitle={`Session #${lectureId} &bull; ${lecture?.subject || "Subject"} (${lecture?.division_name || "Division"})`}
        breadcrumbs={[
          { label: "Lectures", href: "/teacher/lectures" },
          { label: `Session #${lectureId}`, href: `/teacher/lectures/${lectureId}` },
          { label: "Review & Finalize" },
        ]}
        actions={
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={loadReviewData}
              disabled={loading}
              className="p-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-[#FFD700]" : ""}`} />
            </button>
            {!isFinalized && (
              <button
                type="button"
                onClick={() => setShowFinalizeModal(true)}
                disabled={roster.length === 0}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-[0_0_15px_rgba(255,215,0,0.2)] transition-all disabled:opacity-40"
              >
                <Lock className="w-3.5 h-3.5" />
                <span>Finalize & Lock Register</span>
              </button>
            )}
          </div>
        }
      >
        {successMessage && (
          <div className="mb-6 p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/60 text-[#7BD88F] text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>{successMessage}</span>
            </div>
            <button type="button" onClick={() => setSuccessMessage(null)}>
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {isFinalized && (
          <div className="mb-6 p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30] text-xs flex items-center justify-between">
            <div className="flex items-center gap-2.5 text-[#F5F5F5]">
              <Lock className="w-4 h-4 text-[#FFD700]" />
              <span>
                Finalized and Immutable: This attendance record is locked by teacher authority.
              </span>
            </div>
            <span className="text-[11px] text-[#A1A1AA]">Read-Only Mode</span>
          </div>
        )}

        {/* ── CLASSROOM IMAGE & YOLO DETECTION OVERLAY INSPECTION ── */}
        {hasPhoto && (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7 shadow-xl mb-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
              <div>
                <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                  COMPUTER VISION DETECTION OVERLAYS
                </span>
                <h3 className="text-base font-bold text-[#F5F5F5]">
                  Classroom Multi-Face Detection Review
                </h3>
              </div>

              {/* Overlay Toggle Controls */}
              <div className="flex items-center gap-2 p-1 bg-[#17171B] border border-[#2A2A30] rounded-2xl">
                <button
                  type="button"
                  onClick={() => setOverlayMode("overlay")}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
                    overlayMode === "overlay"
                      ? "bg-[#FFD700] text-[#0B0B0D] font-bold shadow-sm"
                      : "text-[#A1A1AA] hover:text-[#F5F5F5]"
                  }`}
                >
                  <ScanFace className="w-3.5 h-3.5" />
                  <span>Detection Overlays</span>
                </button>
                <button
                  type="button"
                  onClick={() => setOverlayMode("clean")}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
                    overlayMode === "clean"
                      ? "bg-[#FFD700] text-[#0B0B0D] font-bold shadow-sm"
                      : "text-[#A1A1AA] hover:text-[#F5F5F5]"
                  }`}
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Clean Photo</span>
                </button>
                <button
                  type="button"
                  onClick={() => setOverlayMode((m) => (m === "hidden" ? "overlay" : "hidden"))}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
                    overlayMode === "hidden"
                      ? "bg-[#2A2A30] text-[#F5F5F5]"
                      : "text-[#A1A1AA] hover:text-[#F5F5F5]"
                  }`}
                >
                  {overlayMode === "hidden" ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                  <span>{overlayMode === "hidden" ? "Show Photo" : "Hide Photo"}</span>
                </button>
              </div>
            </div>

            {/* Overlays Legend Bar */}
            {overlayMode !== "hidden" && (
              <>
                <div className="flex flex-wrap items-center gap-3 p-3 mb-4 rounded-2xl bg-[#17171B] border border-[#2A2A30] text-[11px]">
                  <span className="text-[#A1A1AA] font-semibold">Overlay Legend:</span>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
                    <span className="text-[#F5F5F5]">Green: Confirmed AI Match</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
                    <span className="text-[#F5F5F5]">Amber: Ambiguous / Low Separation</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444]" />
                    <span className="text-[#F5F5F5]">Red: Unknown Face</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#8B5CF6]" />
                    <span className="text-[#F5F5F5]">Purple: Duplicate Suppressed</span>
                  </div>
                </div>

                {/* Classroom Image Container */}
                <div className="relative rounded-2xl overflow-hidden border border-[#2A2A30] bg-[#0B0B0D] max-h-[520px] flex items-center justify-center">
                  {currentPhotoSrc ? (
                    <img
                      src={currentPhotoSrc}
                      alt="Classroom face detection view"
                      className="w-full h-auto max-h-[520px] object-contain rounded-2xl"
                    />
                  ) : (
                    <div className="py-20 text-center text-xs text-[#A1A1AA]">
                      <Camera className="w-8 h-8 text-[#FFD700] mx-auto mb-2 opacity-50" />
                      <span>Classroom photograph processing...</span>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {/* Tab Filters & Breakdown Strip */}
        <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-4 mb-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            {[
              { id: "all", label: "All Eligible Students", count: roster.length },
              { id: "flagged", label: "Needs Review", count: flaggedCount, isWarning: true },
              { id: "present", label: "Confirmed Present", count: presentCount },
              ...(pendingCount > 0 ? [{ id: "pending", label: "Pending Verification", count: pendingCount, isInfo: true }] : []),
              { id: "absent", label: "Marked Absent", count: absentCount },
            ].map((tab: any) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                  activeTab === tab.id
                    ? "bg-[#17171B] text-[#FFD700] border border-[#2A2A30] shadow-sm"
                    : "text-[#A1A1AA] hover:text-[#F5F5F5]"
                }`}
              >
                <span>{tab.label}</span>
                <span
                  className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                    tab.isWarning && tab.count > 0
                      ? "bg-amber-950 text-[#FFD700] border border-amber-800"
                      : tab.isInfo && tab.count > 0
                      ? "bg-sky-950 text-sky-400 border border-sky-800"
                      : "bg-[#111114] text-[#A1A1AA]"
                  }`}
                >
                  {tab.count}
                </span>
              </button>
            ))}
          </div>

          <div className="text-xs text-[#A1A1AA]">
            Enrolled division cohort: <strong className="text-[#F5F5F5]">{lecture?.division_name || "—"}</strong>
          </div>
        </div>

        {/* Verification Roster Table */}
        {loading ? (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-12 text-center text-xs text-[#A1A1AA]">
            <Loader2 className="w-5 h-5 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Loading verification roster from FastAPI...</span>
          </div>
        ) : error ? (
          <EmptyState
            icon={AlertCircle}
            title="Database Connection Notice"
            description={`${error} No simulated records are presented per the No-Dummy-Data policy.`}
            action={
              <button
                type="button"
                onClick={loadReviewData}
                className="px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
              >
                Retry Request
              </button>
            }
          />
        ) : filteredRoster.length === 0 ? (
          <EmptyState
            icon={ShieldCheck}
            title="No Matching Students in Roster"
            description="All eligible division students have been processed, or no records match this tab filter."
          />
        ) : (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-[#17171B] text-[#A1A1AA] border-b border-[#2A2A30]">
                    <th className="py-3.5 px-4 font-semibold">Roll No</th>
                    <th className="py-3.5 px-4 font-semibold">Student Name</th>
                    <th className="py-3.5 px-4 font-semibold">Daily RFID Tap</th>
                    <th className="py-3.5 px-4 font-semibold">AI Face Vision</th>
                    <th className="py-3.5 px-4 font-semibold">Match Confidence</th>
                    <th className="py-3.5 px-4 font-semibold">Current Status</th>
                    <th className="py-3.5 px-4 font-semibold">Source</th>
                    {!isFinalized && (
                      <th className="py-3.5 px-4 font-semibold text-right">Faculty Authority Action</th>
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2A2A30]/50 text-[#F5F5F5]">
                  {filteredRoster.map((item) => (
                    <tr
                      key={item.student_id}
                      className={`hover:bg-[#17171B]/50 transition-colors ${
                        item.attendance_status === "FLAGGED" ? "bg-amber-950/10" : ""
                      }`}
                    >
                      <td className="py-3.5 px-4 font-bold text-[#FFD700]">{item.roll_number}</td>
                      <td className="py-3.5 px-4 font-medium">{item.student_name}</td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5">
                          <Radio className="w-3.5 h-3.5 text-[#FFD700]" />
                          <span
                            className={
                              item.daily_rfid_status === "CHECKED_IN"
                                ? "text-[#7BD88F] font-semibold"
                                : "text-[#A1A1AA]"
                            }
                          >
                            {item.daily_rfid_status === "CHECKED_IN"
                              ? `Tapped (${item.daily_check_in_time || "Gate"})`
                              : "No Gate Tap"}
                          </span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5">
                          <ScanFace className="w-3.5 h-3.5 text-[#A1A1AA]" />
                          <span
                            className={
                              item.ai_verification_status === "VERIFIED"
                                ? "text-[#7BD88F]"
                                : item.ai_verification_status === "FLAGGED"
                                ? "text-[#FFD700]"
                                : "text-[#A1A1AA]"
                            }
                          >
                            {item.ai_verification_status}
                          </span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[11px] text-[#A1A1AA]">
                        {item.confidence_score !== null && item.confidence_score !== undefined
                          ? `${(item.confidence_score * 100).toFixed(1)}%`
                          : "—"}
                      </td>
                      <td className="py-3.5 px-4">
                        <StatusBadge status={item.attendance_status.toLowerCase()} />
                      </td>
                      <td className="py-3.5 px-4 text-[10px] text-[#A1A1AA]">
                        {item.verification_source}
                      </td>

                      {/* Faculty Action Buttons (Disabled after finalization) */}
                      {!isFinalized && (
                        <td className="py-3.5 px-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              type="button"
                              onClick={() => handleUpdateStudentStatus(item.student_id, "PRESENT")}
                              className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all ${
                                item.attendance_status === "PRESENT"
                                  ? "bg-emerald-600 text-white shadow-sm"
                                  : "bg-[#17171B] border border-[#2A2A30] text-[#7BD88F] hover:bg-emerald-950/40"
                              }`}
                              title="Confirm Present"
                            >
                              Present
                            </button>
                            <button
                              type="button"
                              onClick={() => handleUpdateStudentStatus(item.student_id, "ABSENT")}
                              className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all ${
                                item.attendance_status === "ABSENT"
                                  ? "bg-red-600 text-white shadow-sm"
                                  : "bg-[#17171B] border border-[#2A2A30] text-red-400 hover:bg-red-950/40"
                              }`}
                              title="Mark Absent"
                            >
                              Absent
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-4 border-t border-[#2A2A30] flex items-center justify-between text-[11px] text-[#A1A1AA]">
              <span>Showing {filteredRoster.length} verified roster entries</span>
              <span>FastAPI Cryptographic Authority &bull; Teacher Review Finalizer</span>
            </div>
          </div>
        )}

        {/* ── FINALIZATION CONFIRMATION MODAL ── */}
        {showFinalizeModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
              className="fixed inset-0 bg-black/80 backdrop-blur-sm"
              onClick={() => setShowFinalizeModal(false)}
            />
            <div className="relative w-full max-w-md bg-[#111114] border border-[#2A2A30] rounded-3xl p-7 shadow-2xl z-10 text-center">
              <div className="w-12 h-12 rounded-full bg-[#17171B] border border-[#FFD700]/40 text-[#FFD700] flex items-center justify-center mx-auto mb-4">
                <Lock className="w-6 h-6" />
              </div>

              <h3 className="text-lg font-bold text-[#F5F5F5]">Finalize Lecture Register?</h3>

              <div className="my-4 p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30] text-xs text-left space-y-2">
                <div className="flex justify-between">
                  <span className="text-[#A1A1AA]">Confirmed Present:</span>
                  <span className="font-bold text-[#7BD88F]">{presentCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#A1A1AA]">Marked Absent:</span>
                  <span className="font-bold text-red-400">{absentCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#A1A1AA]">Unresolved Flags:</span>
                  <span className={`font-bold ${flaggedCount > 0 ? "text-[#FFD700]" : "text-[#A1A1AA]"}`}>
                    {flaggedCount}
                  </span>
                </div>
              </div>

              <p className="text-xs text-[#A1A1AA] leading-relaxed mb-6">
                <strong>Important:</strong> Finalizing this session will lock all attendance statuses permanently. The FastAPI backend enforces record immutability to prevent post-lecture tampering.
              </p>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  disabled={finalizing}
                  onClick={() => setShowFinalizeModal(false)}
                  className="flex-1 py-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA]"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={finalizing}
                  onClick={handleFinalizeRegister}
                  className="flex-1 py-2.5 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md flex items-center justify-center gap-1.5"
                >
                  {finalizing ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Locking...</span>
                    </>
                  ) : (
                    <span>Confirm & Lock</span>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </DashboardLayout>
    </ProtectedPage>
  );
}
