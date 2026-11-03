"use client";

import React, { useState, useEffect, type FormEvent } from "react";
import Link from "next/link";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { deviceService, DeviceRecord } from "@/lib/services";
import { ApiError } from "@/lib/api";
import {
  Radio,
  Plus,
  RefreshCw,
  AlertCircle,
  Cpu,
  ExternalLink,
  X,
  CheckCircle2
} from "lucide-react";

export default function DeviceManagementPage() {
  const [devices, setDevices] = useState<DeviceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formId, setFormId] = useState("");
  const [formName, setFormName] = useState("");
  const [formLocation, setFormLocation] = useState("");
  const [formIp, setFormIp] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  async function loadDevices() {
    setLoading(true);
    setError(null);
    try {
      const data = await deviceService.getAll();
      setDevices(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to connect to FastAPI /devices endpoint.");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDevices();
  }, []);

  async function handleRegisterDevice(e: FormEvent) {
    e.preventDefault();
    if (submitting) return;

    setSubmitting(true);
    try {
      await deviceService.register({
        device_id: formId.trim(),
        device_name: formName.trim(),
        location: formLocation.trim(),
        ip_address: formIp.trim() || undefined,
        status: "online",
      });
      setActionMessage(`RFID Gateway device "${formName}" enrolled successfully.`);
      setIsModalOpen(false);
      setFormId("");
      setFormName("");
      setFormLocation("");
      setFormIp("");
      loadDevices();
    } catch (err: unknown) {
      alert(err instanceof ApiError ? err.message : "Failed to register gateway device.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <ProtectedPage requiredRole="admin">
      <DashboardLayout
        role="admin"
        title="RFID Gateway Infrastructure"
        subtitle="ESP8266 NodeMCU & RC522 reader status, campus ingress gates, and Wi-Fi connectivity."
        breadcrumbs={[{ label: "RFID Devices" }]}
        actions={
          <div className="flex items-center gap-3">
            <Link
              href="/kiosk"
              target="_blank"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#17171B] hover:bg-[#1F1F24] border border-[#2A2A30] text-xs font-semibold text-[#FFD700] hover:border-[#FFD700]/40 transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Open Kiosk Mode</span>
            </Link>
            <button
              type="button"
              onClick={loadDevices}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-[#FFD700]" : ""}`} />
              <span>Ping Status</span>
            </button>
            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Register Hardware</span>
            </button>
          </div>
        }
      >
        {actionMessage && (
          <div className="mb-6 p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/60 text-[#7BD88F] text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>{actionMessage}</span>
            </div>
            <button type="button" onClick={() => setActionMessage(null)}>
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Technical Architecture Info Banner */}
        <div className="mb-8 p-5 rounded-2xl bg-[#111114] border border-[#2A2A30] flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#17171B] border border-[#2A2A30] text-[#FFD700] flex items-center justify-center shrink-0">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-[#F5F5F5]">Hardware Gateway Specifications</h4>
              <p className="text-xs text-[#A1A1AA] mt-0.5">
                Target Microcontroller: ESP8266 (NodeMCU) &bull; Reader: MFRC522 SPI 13.56 MHz &bull; Protocol: REST/HTTP POST to FastAPI
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-[#A1A1AA]">
            <span className="w-2 h-2 rounded-full bg-[#7BD88F]" />
            <span>FastAPI Ingestion Endpoint: <code className="text-[#FFD700]">/api/kiosk/scan</code></span>
          </div>
        </div>

        {loading ? (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-12 text-center text-xs text-[#A1A1AA]">
            <RefreshCw className="w-6 h-6 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Polling hardware gateway statuses...</span>
          </div>
        ) : error ? (
          <EmptyState
            icon={AlertCircle}
            title="Gateway Service Notice"
            description={`${error} No simulated hardware is displayed without live database authorization.`}
            action={
              <button
                type="button"
                onClick={loadDevices}
                className="px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
              >
                Retry Heartbeat
              </button>
            }
          />
        ) : devices.length === 0 ? (
          <EmptyState
            icon={Radio}
            title="No RFID Terminals Enrolled"
            description="The institution has not registered any ESP8266 + RC522 gateway devices. Register your physical campus devices above."
            action={
              <button
                type="button"
                onClick={() => setIsModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
              >
                <Plus className="w-4 h-4" />
                <span>Register Terminal</span>
              </button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {devices.map((dev) => (
              <div
                key={dev.id}
                className="bg-[#111114] border border-[#2A2A30] hover:border-[#FFD700]/40 rounded-2xl p-6 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="px-2.5 py-1 rounded-lg bg-[#17171B] border border-[#2A2A30] text-xs font-mono font-bold text-[#FFD700]">
                      {dev.device_id}
                    </span>
                    <StatusBadge status={dev.status} />
                  </div>

                  <h3 className="text-base font-bold text-[#F5F5F5] mb-1">{dev.device_name}</h3>
                  <p className="text-xs text-[#A1A1AA] mb-4">{dev.location}</p>

                  <div className="space-y-2 py-3 border-y border-[#2A2A30]/60 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-[#A1A1AA]">IP Address</span>
                      <span className="font-mono text-[#F5F5F5]">{dev.ip_address || "DHCP Allocated"}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[#A1A1AA]">MAC Address</span>
                      <span className="font-mono text-[#A1A1AA]">{dev.mac_address || "—"}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[#A1A1AA]">Firmware</span>
                      <span className="text-[#F5F5F5]">{dev.firmware_version || "SmartAttend-NodeMCU-v1.2"}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-2 text-[11px] text-[#A1A1AA] flex items-center justify-between">
                  <span>Last Heartbeat:</span>
                  <span className="text-[#F5F5F5]">{dev.last_ping || "Just now"}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setIsModalOpen(false)} />
            <div className="relative w-full max-w-md bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-8 shadow-2xl z-10">
              <div className="flex items-center justify-between pb-5 border-b border-[#2A2A30] mb-6">
                <h3 className="text-lg font-bold text-[#F5F5F5]">Register RFID Terminal</h3>
                <button type="button" onClick={() => setIsModalOpen(false)} className="p-1.5 text-[#A1A1AA]">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleRegisterDevice} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Device ID *</label>
                  <input
                    type="text"
                    required
                    value={formId}
                    onChange={(e) => setFormId(e.target.value)}
                    placeholder="e.g. ESP8266-GATE-01"
                    className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] font-mono focus:border-[#FFD700] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Friendly Name *</label>
                  <input
                    type="text"
                    required
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder="e.g. Main Entrance Turnstile A"
                    className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Physical Location *</label>
                  <input
                    type="text"
                    required
                    value={formLocation}
                    onChange={(e) => setFormLocation(e.target.value)}
                    placeholder="e.g. Campus North Gate Building 1"
                    className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Static IP Address</label>
                  <input
                    type="text"
                    value={formIp}
                    onChange={(e) => setFormIp(e.target.value)}
                    placeholder="e.g. 192.168.1.120"
                    className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] font-mono focus:border-[#FFD700] focus:outline-none"
                  />
                </div>

                <div className="pt-4 flex items-center justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2.5 rounded-xl bg-[#17171B] text-xs font-semibold text-[#A1A1AA]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-6 py-2.5 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs"
                  >
                    {submitting ? "Registering..." : "Enroll Device"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </DashboardLayout>
    </ProtectedPage>
  );
}
