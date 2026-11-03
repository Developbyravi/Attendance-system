"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Logo from "@/components/Logo";
import { deviceService, checkInService, DailyCheckInRecord } from "@/lib/services";

import {
  Radio,
  WifiOff,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ArrowLeft,
  Cpu,
  ShieldCheck
} from "lucide-react";

export type KioskStatus = "idle" | "success" | "duplicate" | "unknown" | "error";

export default function RfidKioskPage() {
  const [deviceOnline, setDeviceOnline] = useState<boolean | null>(null);
  const [lastPingTime, setLastPingTime] = useState<string>("");
  const [recentScans, setRecentScans] = useState<DailyCheckInRecord[]>([]);
  const [loading, setLoading] = useState(true);

  // Kiosk display status
  const [status, setStatus] = useState<KioskStatus>("idle");
  const [activeScanData, setActiveScanData] = useState<{
    student_name?: string;
    roll_number?: string;
    time?: string;
    message?: string;
  } | null>(null);

  // Poll device connection status from FastAPI
  async function pollHardwareStatus() {
    try {
      const res = await deviceService.getKioskStatus();
      setDeviceOnline(res.status === "online");
      setLastPingTime(res.timestamp || new Date().toLocaleTimeString());
    } catch {
      // Hardware gateway is offline or endpoint awaiting backend
      setDeviceOnline(false);
      setLastPingTime(new Date().toLocaleTimeString());
    }
  }

  // Load actual recent check-ins
  async function loadRecentCheckins() {
    try {
      const logs = await checkInService.getToday();
      setRecentScans(logs.slice(0, 5));
    } catch {
      // Empty or offline
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    pollHardwareStatus();
    loadRecentCheckins();

    const interval = setInterval(() => {
      pollHardwareStatus();
      loadRecentCheckins();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#08080A] text-[#F5F5F5] flex flex-col justify-between p-6 sm:p-10 font-sans select-none overflow-hidden">
      {/* ── TOP HEADER ── */}
      <div className="max-w-6xl w-full mx-auto flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Logo size="md" />
          <div className="hidden sm:block h-6 w-px bg-[#2A2A30]" />
          <span className="hidden sm:inline-block text-xs font-bold text-[#FFD700] tracking-widest uppercase">
            CAMPUS RFID INGRESS TERMINAL
          </span>
        </div>

        {/* Live Device Hardware Status Indicator */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#111114] border border-[#2A2A30] text-xs">
            <Cpu className="w-3.5 h-3.5 text-[#FFD700]" />
            <span className="text-[#A1A1AA] hidden sm:inline">ESP8266 NodeMCU:</span>
            {deviceOnline === null ? (
              <span className="text-[#A1A1AA]">Polling...</span>
            ) : deviceOnline ? (
              <span className="text-[#7BD88F] font-bold flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#7BD88F] animate-pulse" />
                Online
              </span>
            ) : (
              <span className="text-amber-400 font-bold flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                Awaiting Hardware Tap
              </span>
            )}
          </div>

          <Link
            href="/login"
            className="text-xs text-[#A1A1AA] hover:text-[#F5F5F5] flex items-center gap-1 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Staff Login</span>
          </Link>
        </div>
      </div>

      {/* ── MAIN TERMINAL DISPLAY ── */}
      <div className="max-w-3xl w-full mx-auto my-auto text-center py-10">
        {/* RFID Tap Target Visual */}
        <div className="relative inline-flex items-center justify-center mb-8">
          {/* Animated Gold Radar Pulse Rings */}
          <div className="absolute w-64 h-64 rounded-full border border-[#FFD700]/15 animate-ping" />
          <div className="absolute w-52 h-52 rounded-full border border-[#FFD700]/25" />

          {/* Core Scanner Sensor Pad */}
          <div className="w-40 h-40 rounded-full bg-[#111114] border-2 border-[#FFD700] flex flex-col items-center justify-center shadow-[0_0_50px_rgba(255,215,0,0.25)] z-10 transition-transform hover:scale-105">
            <Radio className="w-14 h-14 text-[#FFD700] mb-1 animate-pulse" />
            <span className="text-[10px] font-bold text-[#FFD700] tracking-widest uppercase">
              RC522 13.56MHz
            </span>
          </div>
        </div>

        {/* Status Messages */}
        {status === "idle" && (
          <div className="space-y-3">
            <h1 className="text-3xl sm:text-4xl font-extrabold text-[#F5F5F5] font-display tracking-tight">
              Tap Your RFID Card
            </h1>
            <p className="text-sm sm:text-base text-[#A1A1AA] max-w-md mx-auto leading-relaxed">
              Place your institutional student ID badge close to the reader antenna to register your daily campus presence.
            </p>
          </div>
        )}

        {status === "success" && (
          <div className="space-y-3 animate-in zoom-in-95 duration-200">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-950/60 border border-emerald-500/40 text-[#7BD88F] text-sm font-bold">
              <CheckCircle2 className="w-4 h-4" />
              <span>Gate Check-in Verified</span>
            </div>
            <h2 className="text-3xl font-extrabold text-[#F5F5F5]">
              {activeScanData?.student_name || "Student"}
            </h2>
            <p className="text-sm text-[#FFD700] font-semibold">
              Roll #{activeScanData?.roll_number} &bull; {activeScanData?.time}
            </p>
          </div>
        )}

        {status === "duplicate" && (
          <div className="space-y-3 animate-in zoom-in-95 duration-200">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-950/60 border border-amber-500/40 text-[#FFD700] text-sm font-bold">
              <AlertTriangle className="w-4 h-4" />
              <span>Already Checked In Today</span>
            </div>
            <h2 className="text-2xl font-extrabold text-[#F5F5F5]">
              {activeScanData?.student_name}
            </h2>
            <p className="text-xs text-[#A1A1AA] max-w-md mx-auto">
              Daily presence has already been recorded for this card today. Duplicate scans do not alter attendance.
            </p>
          </div>
        )}

        {status === "unknown" && (
          <div className="space-y-3 animate-in zoom-in-95 duration-200">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-950/60 border border-red-500/40 text-red-400 text-sm font-bold">
              <XCircle className="w-4 h-4" />
              <span>Unrecognized RFID Card</span>
            </div>
            <h2 className="text-2xl font-extrabold text-[#F5F5F5]">Card Not Registered</h2>
            <p className="text-xs text-[#A1A1AA] max-w-md mx-auto">
              This badge UID is not paired with an active student. Please register your card at the Administration office.
            </p>
          </div>
        )}

        {status === "error" && (
          <div className="space-y-3 animate-in zoom-in-95 duration-200">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-950/60 border border-red-500/40 text-red-400 text-sm font-bold">
              <WifiOff className="w-4 h-4" />
              <span>Gateway Communication Error</span>
            </div>
            <h2 className="text-xl font-bold text-[#F5F5F5]">Terminal Offline</h2>
            <p className="text-xs text-[#A1A1AA] max-w-md mx-auto">
              Unable to reach FastAPI backend on port 8001. Please report to Campus IT.
            </p>
          </div>
        )}

        {/* Hardware Notice per Master Prompt Section 13 */}
        <div className="mt-8 text-xs text-[#A1A1AA]/60 flex items-center justify-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-[#FFD700]" />
          <span>Real-time Wi-Fi Ingestion via ESP8266 REST API &bull; No Browser Hardware Emulation</span>
        </div>
      </div>

      {/* ── RECENT INGRESS SCANS TICKER ── */}
      <div className="max-w-4xl w-full mx-auto">
        <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-4">
          <div className="flex items-center justify-between mb-3 text-xs">
            <span className="font-bold text-[#FFD700] uppercase tracking-wider text-[11px]">
              RECENT GATE CHECK-INS
            </span>
            <span className="text-[#A1A1AA] text-[11px]">
              {recentScans.length} verified scans recorded today
            </span>
          </div>

          {recentScans.length === 0 ? (
            <p className="text-xs text-[#A1A1AA] italic text-center py-2">
              Waiting for incoming student badge taps from campus readers...
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 text-xs">
              {recentScans.map((scan) => (
                <div
                  key={scan.id}
                  className="bg-[#17171B] border border-[#2A2A30] rounded-xl p-2.5 flex items-center justify-between"
                >
                  <div className="truncate">
                    <div className="font-bold text-[#F5F5F5] truncate">{scan.student_name}</div>
                    <div className="text-[10px] text-[#A1A1AA]">Roll #{scan.roll_number}</div>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-[11px] text-[#7BD88F] font-bold block">
                      {scan.check_in_time}
                    </span>
                    <span className="text-[9px] text-[#A1A1AA] font-mono">{scan.device_id}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
