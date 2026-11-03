"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import StatCard from "@/components/StatCard";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { useAuth } from "@/context/AuthContext";
import { statsService, NotificationRecord } from "@/lib/services";
import { ApiError } from "@/lib/api";
import {
  Users,
  GraduationCap,
  Radio,
  Calendar,
  XCircle,
  MessageSquare,
  ArrowRight,
  RefreshCw,
  AlertCircle
} from "lucide-react";

export default function ParentDashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<{
    children: Array<{
      id: string | number;
      name: string;
      roll_number: string;
      division_name: string;
      today_checked_in: boolean;
      today_time?: string;
      overall_percentage: number;
      recent_absences: number;
    }>;
    notifications: NotificationRecord[];
  } | null>(null);

  const [selectedChildIndex, setSelectedChildIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadParentData() {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const res = await statsService.getParentChildOverview(user.id);
      setData(res);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to connect to FastAPI /parent/:id/overview endpoint.");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadParentData();
  }, [user]);

  const children = data?.children || [];
  const activeChild = children[selectedChildIndex] || null;

  return (
    <ProtectedPage requiredRole="parent">
      <DashboardLayout
        role="parent"
        title="Parent & Guardian Portal"
        subtitle="Live oversight of your student's campus attendance, gate arrivals, and academic standing."
        breadcrumbs={[{ label: "Overview" }]}
        actions={
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={loadParentData}
              disabled={loading}
              className="p-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-[#FFD700]" : ""}`} />
            </button>
            <Link
              href="/parent/attendance"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md transition-all"
            >
              <span>View Child Register</span>
              <ArrowRight className="w-3.5 h-3.5" />
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
                {error} — All child records are strictly restricted to verified parent-student relationships via Supabase RLS.
              </p>
            </div>
          </div>
        )}

        {loading ? (
          <div className="py-16 text-center text-xs text-[#A1A1AA]">
            <RefreshCw className="w-5 h-5 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Querying verified linked child profiles...</span>
          </div>
        ) : children.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No Linked Student Records Found"
            description="Your guardian account does not currently have any active students linked in the database. Please contact the campus administration to pair your student's roll number."
          />
        ) : (
          <div className="space-y-8">
            {/* Child Selector (when multiple children exist) */}
            {children.length > 1 && (
              <div className="flex items-center gap-3 bg-[#111114] border border-[#2A2A30] rounded-2xl p-3">
                <span className="text-xs font-semibold text-[#A1A1AA]">Select Child:</span>
                <div className="flex gap-2">
                  {children.map((child, idx) => (
                    <button
                      key={child.id}
                      type="button"
                      onClick={() => setSelectedChildIndex(idx)}
                      className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all ${
                        selectedChildIndex === idx
                          ? "bg-[#FFD700] text-[#0B0B0D] shadow-sm"
                          : "bg-[#17171B] text-[#A1A1AA] hover:text-[#F5F5F5]"
                      }`}
                    >
                      {child.name} ({child.division_name})
                    </button>
                  ))}
                </div>
              </div>
            )}

            {activeChild && (
              <>
                {/* Active Child Ingress Status Card */}
                <div className="p-6 rounded-3xl bg-[#111114] border border-[#2A2A30] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div
                      className={`w-12 h-12 rounded-2xl border flex items-center justify-center shrink-0 ${
                        activeChild.today_checked_in
                          ? "bg-emerald-950/40 border-emerald-800/60 text-[#7BD88F]"
                          : "bg-[#17171B] border-[#2A2A30] text-[#A1A1AA]"
                      }`}
                    >
                      <Radio className="w-6 h-6" />
                    </div>
                    <div>
                      <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-0.5">
                        CAMPUS GATE INGRESS
                      </span>
                      <h3 className="text-base font-bold text-[#F5F5F5]">
                        {activeChild.name} &bull; Roll #{activeChild.roll_number}
                      </h3>
                      <p className="text-xs text-[#A1A1AA] mt-0.5">
                        {activeChild.today_checked_in
                          ? `RFID Gate Check-in recorded today at ${activeChild.today_time || "Turnstile Gate"}`
                          : "No RFID check-in tap registered at the campus gates yet today."}
                      </p>
                    </div>
                  </div>

                  <StatusBadge
                    status={activeChild.today_checked_in ? "verified" : "pending"}
                    labelOverride={activeChild.today_checked_in ? "At Campus" : "Not Tapped"}
                  />
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <StatCard
                    label="Current Attendance"
                    value={`${activeChild.overall_percentage}%`}
                    subtext={
                      activeChild.overall_percentage >= 75
                        ? "Satisfies 75% Statutory Minimum"
                        : "Below 75% Attendance Requirement"
                    }
                    trend={activeChild.overall_percentage >= 75 ? "Compliant" : "Defaulter Risk"}
                    trendPositive={activeChild.overall_percentage >= 75}
                    icon={GraduationCap}
                  />
                  <StatCard
                    label="Classroom Division"
                    value={activeChild.division_name}
                    subtext="Enrolled batch"
                    icon={Calendar}
                  />
                  <StatCard
                    label="Recent Absences"
                    value={activeChild.recent_absences}
                    subtext="Missed lecture sessions"
                    icon={XCircle}
                  />
                </div>
              </>
            )}

            {/* WhatsApp Integration Notice Section */}
            <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7 space-y-4">
              <div className="flex items-center gap-2.5 text-xs font-bold text-[#FFD700]">
                <MessageSquare className="w-4 h-4" />
                <span>INSTITUTIONAL WHATSAPP NOTIFICATION DISPATCH</span>
              </div>
              <h3 className="text-base font-bold text-[#F5F5F5]">Automated Alert Dispatch</h3>
              <p className="text-xs text-[#A1A1AA] leading-relaxed max-w-2xl">
                AIoT SmartAttend is engineered to transmit instant automated alerts for daily gate check-in, absence warnings, and weekly attendance digests directly to parents via WhatsApp.
              </p>
              <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#A1A1AA] flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-[#FFD700] shrink-0 mt-0.5" />
                <div>
                  <strong className="text-[#F5F5F5]">Messaging Gateway Status:</strong> WhatsApp dispatch service is currently awaiting campus Gupshup/Twilio API credential provisioning. In accordance with our No-Dummy-Data policy, no fake delivery logs are simulated.
                </div>
              </div>
              <Link
                href="/parent/notifications"
                className="inline-flex items-center gap-1.5 text-xs font-bold text-[#FFD700] hover:text-[#FFE34D]"
              >
                <span>Configure Notification Preferences</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        )}
      </DashboardLayout>
    </ProtectedPage>
  );
}
