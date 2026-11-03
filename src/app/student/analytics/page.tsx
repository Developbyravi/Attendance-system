"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import StatCard from "@/components/StatCard";
import EmptyState from "@/components/EmptyState";
import { useAuth } from "@/context/AuthContext";
import { statsService } from "@/lib/services";
import {
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  RefreshCw
} from "lucide-react";

export default function StudentAnalyticsPage() {
  const { user } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    statsService
      .getStudentStats(user.id)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  const percentage = data?.attendance_percentage || 0;
  const isCompliant = percentage >= 75;

  return (
    <ProtectedPage requiredRole="student">
      <DashboardLayout
        role="student"
        title="Attendance Analytics"
        subtitle="Detailed compliance tracking and statutory attendance metrics."
        breadcrumbs={[{ label: "Analytics" }]}
      >
        {loading ? (
          <div className="py-16 text-center text-xs text-[#A1A1AA]">
            <RefreshCw className="w-5 h-5 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Calculating attendance analytics...</span>
          </div>
        ) : !data || data.total_lectures === 0 ? (
          <EmptyState
            icon={BarChart3}
            title="Insufficient Attendance Data"
            description="Attendance analytics require recorded lecture sessions. Once faculty members publish attendance, compliance metrics will be charted here automatically."
          />
        ) : (
          <div className="max-w-4xl space-y-6">
            {/* Compliance Banner */}
            <div
              className={`p-6 rounded-3xl border flex items-center justify-between ${
                isCompliant
                  ? "bg-emerald-950/30 border-emerald-800/60 text-[#7BD88F]"
                  : "bg-amber-950/30 border-amber-800/60 text-[#FFD700]"
              }`}
            >
              <div className="flex items-center gap-3.5">
                {isCompliant ? (
                  <CheckCircle2 className="w-6 h-6 shrink-0" />
                ) : (
                  <AlertTriangle className="w-6 h-6 shrink-0" />
                )}
                <div>
                  <h3 className="text-base font-bold text-[#F5F5F5]">
                    {isCompliant ? "Attendance In Good Standing" : "Attendance Defaulter Warning"}
                  </h3>
                  <p className="text-xs text-[#A1A1AA] mt-0.5">
                    {isCompliant
                      ? "Your current attendance is above the university 75% minimum threshold."
                      : "Your attendance is currently below 75%. Attend upcoming sessions to restore compliance."}
                  </p>
                </div>
              </div>
              <span className="text-2xl font-extrabold tabular-nums text-[#F5F5F5]">{percentage}%</span>
            </div>

            {/* Progress Visualization */}
            <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7 space-y-4">
              <div className="flex justify-between items-center text-xs font-semibold">
                <span className="text-[#A1A1AA]">Statutory Benchmark Progress</span>
                <span className="text-[#FFD700]">{percentage}% of 100%</span>
              </div>
              <div className="w-full bg-[#17171B] h-3 rounded-full overflow-hidden border border-[#2A2A30]">
                <div
                  className={`h-full transition-all duration-500 ${
                    isCompliant
                      ? "bg-gradient-to-r from-[#C9A227] to-[#FFD700]"
                      : "bg-gradient-to-r from-red-600 to-amber-500"
                  }`}
                  style={{ width: `${Math.min(100, percentage)}%` }}
                />
              </div>
              <div className="flex justify-between text-[11px] text-[#A1A1AA]">
                <span>0%</span>
                <span className="text-[#FFD700] font-bold">75% Cutoff</span>
                <span>100%</span>
              </div>
            </div>

            {/* Detailed Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <StatCard
                label="Eligible Lectures"
                value={data.total_lectures}
                subtext="Total completed"
                icon={Calendar}
              />
              <StatCard
                label="Attended"
                value={data.present_count}
                subtext="Verified present"
                icon={CheckCircle2}
              />
              <StatCard
                label="Absences"
                value={data.absent_count}
                subtext="Recorded missed"
                icon={AlertTriangle}
              />
            </div>
          </div>
        )}
      </DashboardLayout>
    </ProtectedPage>
  );
}
