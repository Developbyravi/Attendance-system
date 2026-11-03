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
  RefreshCw,
  Users
} from "lucide-react";

export default function ParentAttendancePage() {
  const { user } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (!user) return;
    statsService
      .getParentChildOverview(user.id)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  const children = data?.children || [];
  const activeChild = children[0] || null;

  return (
    <ProtectedPage requiredRole="parent">
      <DashboardLayout
        role="parent"
        title="Student Attendance Record"
        subtitle={`Viewing verified lecture attendance records for ${activeChild?.name || "linked student"}.`}
        breadcrumbs={[{ label: "Attendance Records" }]}
      >
        {loading ? (
          <div className="py-16 text-center text-xs text-[#A1A1AA]">
            <RefreshCw className="w-5 h-5 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Retrieving linked student attendance registers...</span>
          </div>
        ) : !activeChild ? (
          <EmptyState
            icon={Users}
            title="No Linked Student Profile"
            description="Your guardian account has no linked students. Contact administration for assistance."
          />
        ) : (
          <div className="space-y-6">
            <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-4 flex items-center justify-between">
              <div>
                <h4 className="text-sm font-bold text-[#F5F5F5]">
                  {activeChild.name} &bull; Roll #{activeChild.roll_number}
                </h4>
                <p className="text-xs text-[#A1A1AA]">
                  Division: {activeChild.division_name} &bull; Overall: {activeChild.overall_percentage}%
                </p>
              </div>
              <StatusBadge
                status={activeChild.overall_percentage >= 75 ? "verified" : "flagged"}
                labelOverride={activeChild.overall_percentage >= 75 ? "Compliant" : "Defaulter Warning"}
              />
            </div>

            <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-10 text-center">
              <Calendar className="w-10 h-10 text-[#FFD700] mx-auto mb-3" />
              <h3 className="text-base font-bold text-[#F5F5F5] mb-1">Lecture Session Ledger</h3>
              <p className="text-xs text-[#A1A1AA] max-w-md mx-auto leading-relaxed">
                Detailed lecture timestamps and faculty verification records are synchronized dynamically from finalized registers.
              </p>
            </div>
          </div>
        )}
      </DashboardLayout>
    </ProtectedPage>
  );
}
