"use client";

import React from "react";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import { useAuth } from "@/context/AuthContext";
import {
  Shield,
  CheckCircle2,
  Lock
} from "lucide-react";

export default function ParentProfilePage() {
  const { user } = useAuth();

  return (
    <ProtectedPage requiredRole="parent">
      <DashboardLayout
        role="parent"
        title="Guardian Profile"
        subtitle="Account credentials and authorized student relationship records."
        breadcrumbs={[{ label: "Profile" }]}
      >
        <div className="max-w-3xl space-y-6">
          <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-7 sm:p-9 shadow-xl">
            <div className="flex items-center gap-5 mb-8">
              <div className="w-16 h-16 rounded-2xl bg-[#FFD700] text-[#0B0B0D] font-bold text-2xl flex items-center justify-center">
                {(user?.full_name?.[0] || "P").toUpperCase()}
              </div>
              <div>
                <h2 className="text-xl font-bold text-[#F5F5F5]">{user?.full_name || user?.username}</h2>
                <p className="text-xs text-[#FFD700] font-semibold mt-0.5">Authorized Guardian</p>
                <p className="text-xs text-[#A1A1AA] mt-1">{user?.email || "Registered Guardian Account"}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                <span className="text-[#A1A1AA] block mb-1">Authorization Status</span>
                <div className="flex items-center gap-1.5 text-[#7BD88F] font-semibold mt-0.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Verified Guardian Account</span>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30]">
                <span className="text-[#A1A1AA] block mb-1">Security Boundary</span>
                <div className="flex items-center gap-1.5 text-[#A1A1AA] font-mono mt-0.5">
                  <Lock className="w-4 h-4 text-[#FFD700]" />
                  <span>Supabase RLS Enforced</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-7 text-xs text-[#A1A1AA] space-y-2">
            <div className="flex items-center gap-2 text-[#FFD700] font-bold">
              <Shield className="w-4 h-4" />
              <span>Guardian Privacy Guarantee</span>
            </div>
            <p className="leading-relaxed">
              Parents are authorized to access records exclusively for students linked to their verified guardian profile. Peer records, biometric embeddings, and administrative parameters remain strictly confidential.
            </p>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedPage>
  );
}
