"use client";

import React, { useState, useEffect, type FormEvent } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { classService, ClassDivisionRecord } from "@/lib/services";
import { ApiError } from "@/lib/api";
import {
  Layers,
  Plus,
  RefreshCw,
  AlertCircle,
  X,
  CheckCircle2
} from "lucide-react";

export default function ClassesManagementPage() {
  const [classes, setClasses] = useState<ClassDivisionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formName, setFormName] = useState("");
  const [formCode, setFormCode] = useState("");
  const [formYear, setFormYear] = useState("2024-2025");
  const [formSemester, setFormSemester] = useState("4");
  const [formDept, setFormDept] = useState("Computer Science & Engineering");
  const [submitting, setSubmitting] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  async function loadClasses() {
    setLoading(true);
    setError(null);
    try {
      const data = await classService.getAll();
      setClasses(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to connect to FastAPI /classes endpoint.");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadClasses();
  }, []);

  async function handleCreateClass(e: FormEvent) {
    e.preventDefault();
    if (submitting) return;

    setSubmitting(true);
    try {
      await classService.create({
        name: formName.trim(),
        code: formCode.trim(),
        academic_year: formYear.trim(),
        semester: formSemester,
        department: formDept,
        is_active: true,
      });
      setActionMessage(`Division "${formName}" created successfully.`);
      setIsModalOpen(false);
      setFormName("");
      setFormCode("");
      loadClasses();
    } catch (err: unknown) {
      alert(err instanceof ApiError ? err.message : "Failed to create division record.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <ProtectedPage requiredRole="admin">
      <DashboardLayout
        role="admin"
        title="Classes & Academic Divisions"
        subtitle="Organize students into department batches, semesters, and active lecture cohorts."
        breadcrumbs={[{ label: "Classes & Divisions" }]}
        actions={
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={loadClasses}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-[#FFD700]" : ""}`} />
              <span>Refresh</span>
            </button>
            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Division</span>
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

        {loading ? (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-12 text-center text-xs text-[#A1A1AA]">
            <RefreshCw className="w-6 h-6 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Retrieving class structures...</span>
          </div>
        ) : error ? (
          <EmptyState
            icon={AlertCircle}
            title="Database Connection Notice"
            description={`${error} In accordance with the No-Dummy-Data policy, no hardcoded sample classes are displayed.`}
            action={
              <button
                type="button"
                onClick={loadClasses}
                className="px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
              >
                Retry
              </button>
            }
          />
        ) : classes.length === 0 ? (
          <EmptyState
            icon={Layers}
            title="No Classes Configured"
            description="The institution database does not currently have any class divisions set up. Create your first academic division above."
            action={
              <button
                type="button"
                onClick={() => setIsModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
              >
                <Plus className="w-4 h-4" />
                <span>Create Division</span>
              </button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {classes.map((cls) => (
              <div
                key={cls.id}
                className="bg-[#111114] border border-[#2A2A30] hover:border-[#FFD700]/40 rounded-2xl p-6 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="px-2.5 py-1 rounded-lg bg-[#17171B] border border-[#2A2A30] text-xs font-bold text-[#FFD700]">
                      {cls.code}
                    </span>
                    <StatusBadge
                      status={cls.is_active ? "verified" : "offline"}
                      labelOverride={cls.is_active ? "Active" : "Archived"}
                    />
                  </div>

                  <h3 className="text-base font-bold text-[#F5F5F5] mb-1">{cls.name}</h3>
                  <p className="text-xs text-[#A1A1AA] mb-4">{cls.department}</p>

                  <div className="space-y-2 py-3 border-y border-[#2A2A30]/60 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-[#A1A1AA]">Semester</span>
                      <span className="font-semibold text-[#F5F5F5]">Sem {cls.semester}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[#A1A1AA]">Academic Year</span>
                      <span className="text-[#F5F5F5]">{cls.academic_year}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[#A1A1AA]">Enrolled Students</span>
                      <span className="font-bold text-[#FFD700]">{cls.total_students || 0}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-2 text-[11px] text-[#A1A1AA]">
                  Faculty Lead: <strong className="text-[#F5F5F5]">{cls.class_teacher || "Unassigned"}</strong>
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
                <h3 className="text-lg font-bold text-[#F5F5F5]">Add Academic Division</h3>
                <button type="button" onClick={() => setIsModalOpen(false)} className="p-1.5 text-[#A1A1AA]">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleCreateClass} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Division Name *</label>
                  <input
                    type="text"
                    required
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder="e.g. AIML-B"
                    className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Division Code *</label>
                    <input
                      type="text"
                      required
                      value={formCode}
                      onChange={(e) => setFormCode(e.target.value)}
                      placeholder="e.g. TE-AIML-B"
                      className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Semester *</label>
                    <input
                      type="number"
                      min="1"
                      max="8"
                      required
                      value={formSemester}
                      onChange={(e) => setFormSemester(e.target.value)}
                      className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Academic Department *</label>
                  <select
                    value={formDept}
                    onChange={(e) => setFormDept(e.target.value)}
                    className="w-full h-10 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                  >
                    <option value="Computer Science & Engineering">Computer Science & Engineering</option>
                    <option value="Artificial Intelligence & Machine Learning">AI & Machine Learning</option>
                    <option value="Information Technology">Information Technology</option>
                    <option value="Electronics & Telecommunication">Electronics & Telecom</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Academic Year *</label>
                  <input
                    type="text"
                    required
                    value={formYear}
                    onChange={(e) => setFormYear(e.target.value)}
                    placeholder="2024-2025"
                    className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
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
                    {submitting ? "Creating..." : "Save Division"}
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
