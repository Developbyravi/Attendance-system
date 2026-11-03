"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import CameraCapture from "@/components/CameraCapture";
import { lectureService, LectureSession, LectureVerificationSummaryResult } from "@/lib/services";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import {
  Camera,
  Upload,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Lock,
  Loader2,
  Video,
  ScanFace,
  Eye,
  X
} from "lucide-react";

export default function LectureDetailsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const { user } = useAuth();
  const resolvedParams = use(params);
  const lectureId = resolvedParams.id;

  const [lecture, setLecture] = useState<LectureSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Capture mode: "camera" | "upload"
  const [captureMode, setCaptureMode] = useState<"camera" | "upload">("camera");

  // File upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [verificationResult, setVerificationResult] = useState<LectureVerificationSummaryResult | null>(null);

  async function loadLecture() {
    setLoading(true);
    setError(null);
    try {
      const data = await lectureService.getById(lectureId);
      setLecture(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to connect to FastAPI /lectures/:id endpoint.");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!user) return;
    loadLecture();
  }, [lectureId, user]);

  async function processClassroomPhoto(_blob: Blob | File, fileObj?: File) {
    const file = (fileObj || _blob) as File;
    if (uploading) return;
    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const res = await lectureService.uploadClassroomPhoto(lectureId, file);
      setVerificationResult(res);
      setUploadSuccess(
        `Classroom capture processed successfully! ${res.detector || "InsightFace SCRFD-10G"} detected ${res.detected_faces} faces: ${res.verified_present} confirmed present, ${res.rfid_only + res.ai_only} flagged for review.`
      );
      loadLecture();
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setUploadError(err.message);
      } else if (err instanceof Error) {
        setUploadError(err.message);
      } else {
        setUploadError("Classroom photo processing failed. Ensure FastAPI vision microservice is online.");
      }
    } finally {
      setUploading(false);
    }
  }

  async function handleUploadPhoto(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFile) return;
    await processClassroomPhoto(selectedFile, selectedFile);
  }

  return (
    <ProtectedPage requiredRole="teacher">
      <DashboardLayout
        role="teacher"
        title={lecture ? `${lecture.subject} — ${lecture.title}` : `Lecture #${lectureId}`}
        subtitle={`Division: ${lecture?.division_name || "—"} &bull; Scheduled: ${lecture?.lecture_date || "—"}`}
        breadcrumbs={[
          { label: "Lectures", href: "/teacher/lectures" },
          { label: `Session #${lectureId}` },
        ]}
        actions={
          lecture && (
            <div className="flex items-center gap-3">
              <StatusBadge status={lecture.status} />
              {lecture.status !== "finalized" ? (
                <Link
                  href={`/teacher/lectures/${lectureId}/review`}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md transition-all"
                >
                  <span>Review Attendance</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              ) : (
                <Link
                  href={`/teacher/lectures/${lectureId}/review`}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#17171B] border border-[#2A2A30] hover:border-[#FFD700]/50 text-[#F5F5F5] font-semibold text-xs transition-all"
                >
                  <Lock className="w-3.5 h-3.5 text-[#FFD700]" />
                  <span>View Locked Records</span>
                </Link>
              )}
            </div>
          )
        }
      >
        {loading ? (
          <div className="py-16 text-center text-xs text-[#A1A1AA]">
            <Loader2 className="w-6 h-6 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Loading lecture session details...</span>
          </div>
        ) : error || !lecture ? (
          <EmptyState
            icon={AlertCircle}
            title="Lecture Record Unavailable"
            description={`${error || "Session not found."} In accordance with No-Dummy-Data policy, no mock lecture is shown.`}
            action={
              <Link
                href="/teacher/lectures"
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
              >
                <span>Back to Lectures List</span>
              </Link>
            }
          />
        ) : (
          <div className="max-w-4xl space-y-6">
            {/* Finalization Notice if locked */}
            {lecture.status === "finalized" && (
              <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30] text-xs flex items-center justify-between">
                <div className="flex items-center gap-2.5 text-[#F5F5F5]">
                  <Lock className="w-4 h-4 text-[#FFD700]" />
                  <span>
                    This lecture attendance record has been finalized and cryptographically locked. No further photo captures or manual modifications are permitted.
                  </span>
                </div>
                <span className="text-[11px] text-[#A1A1AA] font-mono">
                  Finalized: {lecture.finalized_at || "Recorded"}
                </span>
              </div>
            )}

            {/* Session Parameters Overview */}
            <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7">
              <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                SESSION PARAMETERS
              </span>
              <h3 className="text-base font-bold text-[#F5F5F5] mb-5">Timetable & Venue Information</h3>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                  <span className="text-[#A1A1AA] block mb-1">Division Cohort</span>
                  <span className="font-bold text-[#FFD700] text-sm">{lecture.division_name}</span>
                </div>
                <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                  <span className="text-[#A1A1AA] block mb-1">Lecture Date</span>
                  <span className="font-bold text-[#F5F5F5] text-sm">{lecture.lecture_date}</span>
                </div>
                <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                  <span className="text-[#A1A1AA] block mb-1">Start Time</span>
                  <span className="font-bold text-[#F5F5F5] text-sm">{lecture.start_time}</span>
                </div>
                <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                  <span className="text-[#A1A1AA] block mb-1">Venue</span>
                  <span className="font-bold text-[#F5F5F5] text-sm">{lecture.classroom || "Assigned Hall"}</span>
                </div>
              </div>
            </div>

            {/* Classroom Photograph & AI Verification Section */}
            {lecture.status !== "finalized" && (
              <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                  <div>
                    <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                      AI FACE VISION PIPELINE
                    </span>
                    <h3 className="text-base font-bold text-[#F5F5F5]">Classroom Attendance Capture</h3>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-[#7BD88F]">
                    <span className="w-2 h-2 rounded-full bg-[#7BD88F]" />
                    <span>Cross-referenced against Daily RFID Taps</span>
                  </div>
                </div>

                <p className="text-xs text-[#A1A1AA] mb-6 leading-relaxed">
                  Capture a live photo of the classroom using your webcam or submit an image file. InsightFace SCRFD-10G detects all usable faces (with 5-point landmark alignment) and ArcFace matches them against enrolled students in division {lecture.division_name}.
                </p>

                {/* Capture Method Switcher */}
                <div className="flex items-center gap-2 mb-6 p-1 bg-[#17171B] border border-[#2A2A30] rounded-2xl w-fit">
                  <button
                    type="button"
                    onClick={() => setCaptureMode("camera")}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                      captureMode === "camera"
                        ? "bg-[#FFD700] text-[#0B0B0D] shadow-sm font-bold"
                        : "text-[#A1A1AA] hover:text-[#F5F5F5]"
                    }`}
                  >
                    <Video className="w-3.5 h-3.5" />
                    <span>Live Camera Stream</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setCaptureMode("upload")}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                      captureMode === "upload"
                        ? "bg-[#FFD700] text-[#0B0B0D] shadow-sm font-bold"
                        : "text-[#A1A1AA] hover:text-[#F5F5F5]"
                    }`}
                  >
                    <Upload className="w-3.5 h-3.5" />
                    <span>Upload Image File</span>
                  </button>
                </div>

                {/* Success Banner */}
                {uploadSuccess && (
                  <div className="mb-6 p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/60 text-[#7BD88F] text-xs flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold text-[#F5F5F5] block">Vision Pipeline Executed</span>
                        <span className="mt-0.5 block">{uploadSuccess}</span>
                      </div>
                    </div>
                    <Link
                      href={`/teacher/lectures/${lectureId}/review`}
                      className="inline-flex items-center gap-1 text-[#FFD700] hover:text-[#FFE34D] font-bold shrink-0 underline"
                    >
                      <span>Review Overlays</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                )}

                {/* Error Banner */}
                {uploadError && (
                  <div className="mb-6 p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold text-[#F5F5F5] block">Capture Processing Failed</span>
                        <span className="mt-0.5 block">{uploadError}</span>
                      </div>
                    </div>
                    <button type="button" onClick={() => setUploadError(null)}>
                      <X className="w-4 h-4 text-[#A1A1AA]" />
                    </button>
                  </div>
                )}

                {/* Mode 1: Live Camera Capture */}
                {captureMode === "camera" && (
                  <div className="space-y-4">
                    <CameraCapture
                      mode="classroom"
                      onCapture={processClassroomPhoto}
                    />
                    {uploading && (
                      <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30] text-center text-xs text-[#A1A1AA] flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin text-[#FFD700]" />
                        <span>Running InsightFace SCRFD-10G detector & ArcFace matching on server...</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Mode 2: File Upload */}
                {captureMode === "upload" && (
                  <form onSubmit={handleUploadPhoto} className="space-y-4">
                    <div className="border-2 border-dashed border-[#2A2A30] hover:border-[#FFD700]/50 rounded-2xl p-8 text-center bg-[#17171B]/50 transition-colors">
                      <Camera className="w-10 h-10 text-[#FFD700] mx-auto mb-3" />
                      <label className="cursor-pointer block">
                        <span className="text-sm font-bold text-[#F5F5F5] hover:text-[#FFD700] transition-colors">
                          {selectedFile ? selectedFile.name : "Select or drag classroom photo (.jpg, .png)"}
                        </span>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => {
                            if (e.target.files?.[0]) setSelectedFile(e.target.files[0]);
                          }}
                          className="hidden"
                        />
                      </label>
                      <p className="text-[11px] text-[#A1A1AA] mt-1.5">
                        Classroom photographs remain private and are stored strictly in authorized Supabase storage.
                      </p>
                    </div>

                    <div className="flex items-center justify-between pt-2">
                      <span className="text-xs text-[#A1A1AA]">
                        {selectedFile ? `Selected: ${(selectedFile.size / 1024 / 1024).toFixed(2)} MB` : "No file chosen"}
                      </span>
                      <button
                        type="submit"
                        disabled={!selectedFile || uploading}
                        className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs tracking-wider shadow-md transition-all disabled:opacity-40"
                      >
                        {uploading ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span>Processing Face Embeddings...</span>
                          </>
                        ) : (
                          <>
                            <Upload className="w-3.5 h-3.5" />
                            <span>Process & Cross-Check</span>
                          </>
                        )}
                      </button>
                    </div>
                  </form>
                )}

                {/* Recent Verification Summary Box */}
                {(verificationResult || lecture.classroom_photo_url) && (
                  <div className="mt-6 p-5 rounded-2xl bg-[#17171B] border border-[#2A2A30] flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      {lecture.overlay_image_url || verificationResult?.overlay_image_url ? (
                        <div className="w-16 h-16 rounded-xl bg-[#0B0B0D] border border-[#2A2A30] overflow-hidden shrink-0 relative">
                          <img
                            src={lecture.overlay_image_url || verificationResult?.overlay_image_url}
                            alt="Classroom overlay thumbnail"
                            className="w-full h-full object-cover"
                          />
                        </div>
                      ) : (
                        <div className="w-16 h-16 rounded-xl bg-[#0B0B0D] border border-[#2A2A30] flex items-center justify-center shrink-0 text-[#FFD700]">
                          <ScanFace className="w-7 h-7" />
                        </div>
                      )}
                      <div>
                        <span className="text-[11px] font-bold text-[#FFD700] uppercase block">
                          DETECTION OVERLAYS READY
                        </span>
                        <h4 className="text-sm font-bold text-[#F5F5F5]">
                          {verificationResult
                            ? `${verificationResult.detected_faces} faces detected & mapped`
                            : "Classroom photo verified"}
                        </h4>
                        <p className="text-xs text-[#A1A1AA] mt-0.5">
                          Visual bounding boxes rendered for recognized, ambiguous, and unknown students.
                        </p>
                      </div>
                    </div>

                    <Link
                      href={`/teacher/lectures/${lectureId}/review`}
                      className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md shrink-0 transition-all"
                    >
                      <Eye className="w-4 h-4" />
                      <span>Inspect Overlays & Roster</span>
                    </Link>
                  </div>
                )}
              </div>
            )}

            {/* Attendance Roster Summary Cards */}
            <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7">
              <div className="flex items-center justify-between mb-5">
                <div>
                  <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                    ROSTER STATUS
                  </span>
                  <h3 className="text-base font-bold text-[#F5F5F5]">Current Attendance Breakdown</h3>
                </div>
                <Link
                  href={`/teacher/lectures/${lectureId}/review`}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-[#FFD700] hover:text-[#FFE34D]"
                >
                  <span>Open Full Review Table</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              <div className={`grid grid-cols-2 ${(lecture.pending_count || 0) > 0 ? "sm:grid-cols-5" : "sm:grid-cols-4"} gap-4 text-center`}>
                <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                  <span className="text-xs text-[#A1A1AA] block mb-1">Eligible Active</span>
                  <span className="text-xl font-bold text-[#F5F5F5]">{lecture.total_enrolled}</span>
                </div>
                <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                  <span className="text-xs text-[#A1A1AA] block mb-1">Present</span>
                  <span className="text-xl font-bold text-[#7BD88F]">{lecture.present_count}</span>
                </div>
                <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                  <span className="text-xs text-[#A1A1AA] block mb-1">Flagged for Review</span>
                  <span className="text-xl font-bold text-[#FFD700]">{lecture.flagged_count}</span>
                </div>
                {(lecture.pending_count || 0) > 0 && (
                  <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                    <span className="text-xs text-[#A1A1AA] block mb-1">Pending Capture</span>
                    <span className="text-xl font-bold text-sky-400">{lecture.pending_count}</span>
                  </div>
                )}
                <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                  <span className="text-xs text-[#A1A1AA] block mb-1">Marked Absent</span>
                  <span className="text-xl font-bold text-red-400">{lecture.absent_count}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </DashboardLayout>
    </ProtectedPage>
  );
}
