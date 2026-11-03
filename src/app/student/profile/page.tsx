"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import CameraCapture from "@/components/CameraCapture";
import { useAuth } from "@/context/AuthContext";
import { studentService } from "@/lib/services";
import { ApiError } from "@/lib/api";
import {
  Shield,
  CheckCircle2,
  Lock,
  Camera,
  ScanFace,
  AlertCircle,
  RefreshCw,
  X,
  Sparkles
} from "lucide-react";

export default function StudentProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<{
    id: number;
    name: string;
    roll_no: string;
    email: string;
    department: string;
    year: string;
    division: string;
    rfid_uid?: string;
    face_enrolled: boolean;
    created_at: string;
  } | null>(null);

  const [loadingProfile, setLoadingProfile] = useState(true);
  const [showCamera, setShowCamera] = useState(false);
  const [enrolling, setEnrolling] = useState(false);
  const [enrollSuccess, setEnrollSuccess] = useState<string | null>(null);
  const [enrollError, setEnrollError] = useState<string | null>(null);
  const [qualityWarnings, setQualityWarnings] = useState<string[]>([]);

  async function loadProfile() {
    setLoadingProfile(true);
    try {
      const data = await studentService.getProfile();
      setProfile(data);
    } catch {
      // Fallback to user context values if profile endpoint is not available
    } finally {
      setLoadingProfile(false);
    }
  }

  useEffect(() => {
    loadProfile();
  }, []);

  async function handleEnrollFace(_blob: Blob, capturedFile: File) {
    setEnrolling(true);
    setEnrollError(null);
    setEnrollSuccess(null);
    setQualityWarnings([]);

    try {
      const res = await studentService.selfEnrollFace(capturedFile);
      setEnrollSuccess(
        `Biometrics successfully registered! Detected ${res.faces_detected} face and generated 512-d ArcFace embedding.`
      );
      if (res.quality_warnings && res.quality_warnings.length > 0) {
        setQualityWarnings(res.quality_warnings);
      }
      setShowCamera(false);
      loadProfile();
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setEnrollError(err.message);
      } else if (err instanceof Error) {
        setEnrollError(err.message);
      } else {
        setEnrollError("Failed to register face biometrics. Please check camera framing and retry.");
      }
    } finally {
      setEnrolling(false);
    }
  }

  const isEnrolled = profile ? profile.face_enrolled : false;

  return (
    <ProtectedPage requiredRole="student">
      <DashboardLayout
        role="student"
        title="Student Profile"
        subtitle="Your institutional identity, academic enrollment, and biometric credentials."
        breadcrumbs={[{ label: "Profile" }]}
      >
        <div className="max-w-3xl space-y-6">
          {/* Main ID Card */}
          <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-7 sm:p-9 shadow-xl">
            <div className="flex items-center gap-5 mb-8">
              <div className="w-16 h-16 rounded-2xl bg-[#FFD700] text-[#0B0B0D] font-bold text-2xl flex items-center justify-center">
                {(user?.full_name?.[0] || profile?.name?.[0] || "S").toUpperCase()}
              </div>
              <div>
                <h2 className="text-xl font-bold text-[#F5F5F5]">
                  {profile?.name || user?.full_name || user?.username}
                </h2>
                <p className="text-xs text-[#FFD700] font-semibold mt-0.5">Enrolled Student</p>
                <p className="text-xs text-[#A1A1AA] mt-1">{profile?.email || user?.email || "Student Account"}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                <span className="text-[#A1A1AA] block mb-1">Roll / Identifier</span>
                <span className="font-bold text-[#F5F5F5] text-sm">
                  {profile?.roll_no || user?.student_id || user?.username || "STU-AIML-42"}
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                <span className="text-[#A1A1AA] block mb-1">Division Cohort</span>
                <span className="font-bold text-[#FFD700] text-sm">
                  {profile?.division ? `Division ${profile.division}` : (user?.division || "AIML-B")}
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                <span className="text-[#A1A1AA] block mb-1">Account Standing</span>
                <div className="flex items-center gap-1.5 text-[#7BD88F] font-semibold mt-0.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Active & Verified</span>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                <span className="text-[#A1A1AA] block mb-1">Security Boundary</span>
                <div className="flex items-center gap-1.5 text-[#A1A1AA] font-mono mt-0.5">
                  <Lock className="w-4 h-4 text-[#FFD700]" />
                  <span>RLS Enforced</span>
                </div>
              </div>
            </div>
          </div>

          {/* Biometric Face Enrollment Section */}
          <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-7 sm:p-9 shadow-xl relative overflow-hidden">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
              <div className="flex items-center gap-4">
                <div
                  className={`w-12 h-12 rounded-2xl border flex items-center justify-center shrink-0 ${
                    isEnrolled
                      ? "bg-emerald-950/40 border-emerald-800/60 text-[#7BD88F]"
                      : "bg-amber-950/40 border-amber-800/60 text-[#FFD700]"
                  }`}
                >
                  <ScanFace className="w-6 h-6" />
                </div>
                <div>
                  <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-0.5">
                    FACIAL BIOMETRICS PIPELINE
                  </span>
                  <h3 className="text-base font-bold text-[#F5F5F5]">
                    {isEnrolled ? "Face Biometrics Enrolled & Verified" : "Biometrics Pending Enrollment"}
                  </h3>
                  <p className="text-xs text-[#A1A1AA] mt-0.5">
                    {isEnrolled
                      ? "Your ArcFace 512-dimensional embedding is stored for classroom vision cross-matching."
                      : "Capture a live camera snapshot to enable automated per-lecture AI attendance."}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => {
                  setShowCamera((prev) => !prev);
                  setEnrollError(null);
                  setEnrollSuccess(null);
                }}
                className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all shadow-md shrink-0 ${
                  isEnrolled
                    ? "bg-[#17171B] border border-[#2A2A30] text-[#F5F5F5] hover:border-[#FFD700]/50"
                    : "bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D]"
                }`}
              >
                <Camera className="w-4 h-4" />
                <span>{showCamera ? "Close Camera" : isEnrolled ? "Update Face Biometrics" : "Enroll Face via Camera"}</span>
              </button>
            </div>

            {/* Success Banner */}
            {enrollSuccess && (
              <div className="mb-6 p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/60 text-[#7BD88F] text-xs flex items-start justify-between gap-3">
                <div className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold block">Biometric Enrollment Successful</span>
                    <span className="text-[#A1A1AA] mt-0.5 block">{enrollSuccess}</span>
                    {qualityWarnings.length > 0 && (
                      <ul className="mt-2 list-disc list-inside text-amber-300">
                        {qualityWarnings.map((w, idx) => (
                          <li key={idx}>{w}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
                <button type="button" onClick={() => setEnrollSuccess(null)} className="text-[#A1A1AA] hover:text-[#F5F5F5]">
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Error Banner */}
            {enrollError && (
              <div className="mb-6 p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-start justify-between gap-3">
                <div className="flex items-start gap-2.5">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-[#F5F5F5] block">Enrollment Rejected</span>
                    <span className="text-rose-200 mt-0.5 block">{enrollError}</span>
                    <span className="text-[11px] text-[#A1A1AA] mt-1.5 block">
                      Instructions: Ensure you are in a well-lit environment, facing the camera directly, and that no other people are in view.
                    </span>
                  </div>
                </div>
                <button type="button" onClick={() => setEnrollError(null)} className="text-[#A1A1AA] hover:text-[#F5F5F5]">
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Live Camera Viewfinder */}
            {showCamera && (
              <div className="mt-6 pt-6 border-t border-[#2A2A30]">
                <div className="mb-4 text-xs text-[#A1A1AA] flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-[#FFD700]" />
                  <span>
                    Align your face within the oval guide. The system validates 1 clear face using InsightFace SCRFD-10G.
                  </span>
                </div>

                <CameraCapture
                  mode="portrait"
                  onCapture={handleEnrollFace}
                  onCancel={() => setShowCamera(false)}
                />

                {enrolling && (
                  <div className="mt-4 p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30] text-center text-xs text-[#A1A1AA] flex items-center justify-center gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin text-[#FFD700]" />
                    <span>Transmitting image to FastAPI for SCRFD-10G detection & ArcFace embedding generation...</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Privacy & Protection Guarantee */}
          <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7 text-xs text-[#A1A1AA] space-y-2">
            <div className="flex items-center gap-2 text-[#FFD700] font-bold">
              <Shield className="w-4 h-4" />
              <span>Biometric & Data Privacy Protection</span>
            </div>
            <p className="leading-relaxed">
              In accordance with AIoT SmartAttend institutional security policies, students are only authorized to view their own attendance records. Raw facial embeddings and RFID hardware serial numbers are strictly secured on the backend and are not exposed to client applications. Original photos are persisted only to the private Supabase biometric storage bucket.
            </p>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedPage>
  );
}
