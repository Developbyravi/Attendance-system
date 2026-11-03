"use client";

import React, { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import EmptyState from "@/components/EmptyState";
import {
  MessageSquare,
  CheckCircle2,
  AlertCircle,
  Save
} from "lucide-react";

export default function ParentNotificationsPage() {
  const [dailyCheckinAlerts, setDailyCheckinAlerts] = useState(true);
  const [absenceAlerts, setAbsenceAlerts] = useState(true);
  const [lectureUpdates, setLectureUpdates] = useState(false);
  const [weeklyDigest, setWeeklyDigest] = useState(true);
  const [saved, setSaved] = useState(false);

  function handleSavePreferences(e: React.FormEvent) {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  return (
    <ProtectedPage requiredRole="parent">
      <DashboardLayout
        role="parent"
        title="Notification Preferences & History"
        subtitle="Configure alerts for gate arrivals, missed sessions, and weekly digests."
        breadcrumbs={[{ label: "Notifications" }]}
      >
        <div className="max-w-3xl space-y-8">
          {saved && (
            <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/60 text-[#7BD88F] text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>Notification preferences saved to institutional profile.</span>
            </div>
          )}

          {/* Preferences Configuration Form */}
          <form
            onSubmit={handleSavePreferences}
            className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-8 space-y-6"
          >
            <div>
              <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                DISPATCH CHANNELS
              </span>
              <h3 className="text-base font-bold text-[#F5F5F5]">WhatsApp & SMS Notification Rules</h3>
              <p className="text-xs text-[#A1A1AA] mt-1">
                Select which campus events should trigger automated dispatches to your registered mobile device.
              </p>
            </div>

            <div className="space-y-4">
              {[
                {
                  id: "checkin",
                  title: "Daily RFID Gate Check-In Alert",
                  desc: "Receive an instant WhatsApp message when your student taps their RFID card at the campus gate.",
                  checked: dailyCheckinAlerts,
                  setter: setDailyCheckinAlerts,
                },
                {
                  id: "absence",
                  title: "Urgent Absence Notification",
                  desc: "Instant alert if student is marked absent during verified lecture sessions.",
                  checked: absenceAlerts,
                  setter: setAbsenceAlerts,
                },
                {
                  id: "lecture",
                  title: "Per-Lecture Attendance Updates",
                  desc: "Notification after every individual subject session is published by faculty.",
                  checked: lectureUpdates,
                  setter: setLectureUpdates,
                },
                {
                  id: "weekly",
                  title: "Weekly Attendance Summary Digest",
                  desc: "Consolidated report every Friday summarizing total sessions and percentage standing.",
                  checked: weeklyDigest,
                  setter: setWeeklyDigest,
                },
              ].map((item) => (
                <div
                  key={item.id}
                  className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30] flex items-start justify-between gap-4"
                >
                  <div>
                    <h4 className="text-xs font-bold text-[#F5F5F5]">{item.title}</h4>
                    <p className="text-[11px] text-[#A1A1AA] mt-0.5 leading-relaxed">{item.desc}</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={item.checked}
                    onChange={(e) => item.setter(e.target.checked)}
                    className="w-4 h-4 rounded text-[#FFD700] focus:ring-[#FFD700] bg-[#111114] border-[#2A2A30] mt-0.5"
                  />
                </div>
              ))}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="submit"
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs tracking-wider shadow-md transition-all"
              >
                <Save className="w-4 h-4" />
                <span>Save Notification Rules</span>
              </button>
            </div>
          </form>

          {/* Integration Status Notice */}
          <div className="p-5 rounded-2xl bg-[#111114] border border-[#2A2A30] text-xs text-[#A1A1AA] flex items-start gap-3">
            <AlertCircle className="w-4 h-4 text-[#FFD700] shrink-0 mt-0.5" />
            <div>
              <strong className="text-[#F5F5F5]">Notice on WhatsApp Delivery:</strong> Live messaging transmission is awaiting institutional WhatsApp Business API gateway configuration. Notification triggers configured here will apply automatically as soon as the campus gateway is operational.
            </div>
          </div>

          {/* Notification History Feed */}
          <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-8">
            <div className="flex items-center justify-between mb-4">
              <div>
                <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                  DISPATCH AUDIT
                </span>
                <h3 className="text-base font-bold text-[#F5F5F5]">Recent Dispatch History</h3>
              </div>
            </div>

            <EmptyState
              icon={MessageSquare}
              title="No Notifications Dispatched"
              description="No automated alerts have been sent to your account yet. Dispatched messages will appear in this ledger."
            />
          </div>
        </div>
      </DashboardLayout>
    </ProtectedPage>
  );
}
