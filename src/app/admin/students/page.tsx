"use client";

import React, { useState, useEffect, type FormEvent } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { studentService, classService, deviceService, rfidService, StudentRecord, ClassDivisionRecord, DeviceRecord, RfidAssignmentSession } from "@/lib/services";
import { ApiError } from "@/lib/api";
import {
  GraduationCap,
  Plus,
  Search,
  Filter,
  Download,
  Trash2,
  Edit2,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  X,
  CreditCard,
  Radio,
  Clock,
  ShieldAlert,
  ShieldCheck,
  RotateCcw,
  Ban,
  Check,
  AlertTriangle
} from "lucide-react";

export default function StudentManagementPage() {
  const [students, setStudents] = useState<StudentRecord[]>([]);
  const [divisions, setDivisions] = useState<ClassDivisionRecord[]>([]);
  const [devices, setDevices] = useState<DeviceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDivision, setSelectedDivision] = useState("");

  // Create / Edit Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<StudentRecord | null>(null);
  const [formRoll, setFormRoll] = useState("");
  const [formName, setFormName] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formDepartment, setFormDepartment] = useState("Computer Science & Engineering");
  const [formYear, setFormYear] = useState("3rd Year");
  const [formDivision, setFormDivision] = useState("A");
  const [formRfid, setFormRfid] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  // Deactivate Student Account Modal State
  const [deactivatingId, setDeactivatingId] = useState<string | number | null>(null);

  // ── RFID Card Assignment Workflow State ──
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [selectedStudentForRfid, setSelectedStudentForRfid] = useState<StudentRecord | null>(null);
  const [assignmentSession, setAssignmentSession] = useState<RfidAssignmentSession | null>(null);
  const [selectedReader, setSelectedReader] = useState("GATE-READER-01");
  const [assignmentTimeoutSec, setAssignmentTimeoutSec] = useState(60);
  const [assignmentLoading, setAssignmentLoading] = useState(false);
  const [assignmentError, setAssignmentError] = useState<string | null>(null);
  const [assignmentReason, setAssignmentReason] = useState("");
  const [assignmentSuccess, setAssignmentSuccess] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(60);

  // ── Card Deactivation Modal State ──
  const [deactivatingCardStudent, setDeactivatingCardStudent] = useState<StudentRecord | null>(null);
  const [deactivateReason, setDeactivateReason] = useState("");
  const [deactivateCardLoading, setDeactivateCardLoading] = useState(false);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [studentList, classList, deviceList] = await Promise.allSettled([
        studentService.getAll({ query: searchQuery || undefined, division_id: selectedDivision || undefined }),
        classService.getAll(),
        deviceService.getAll(),
      ]);

      if (studentList.status === "fulfilled") {
        setStudents(studentList.value);
      } else {
        setError("Could not retrieve student list from FastAPI /students endpoint.");
      }

      if (classList.status === "fulfilled") {
        setDivisions(classList.value);
      }

      if (deviceList.status === "fulfilled" && deviceList.value.length > 0) {
        setDevices(deviceList.value);
      }
    } catch {
      setError("Failed to fetch records. Backend service may be offline.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [selectedDivision]);

  // ── Live Polling & Timer for Pending RFID Scan ──
  useEffect(() => {
    if (!isAssignModalOpen || !assignmentSession || assignmentSession.status !== "PENDING_SCAN") {
      return;
    }

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    const poller = setInterval(async () => {
      try {
        const session = await rfidService.getSessionStatus(assignmentSession.session_id);
        setAssignmentSession(session);
        if (session.status === "SCANNED") {
          clearInterval(poller);
          clearInterval(timer);
        } else if (session.status === "EXPIRED" || session.status === "CANCELLED") {
          clearInterval(poller);
          clearInterval(timer);
        }
      } catch {
        // Polling gracefully ignores transient network hiccups
      }
    }, 1500);

    return () => {
      clearInterval(timer);
      clearInterval(poller);
    };
  }, [isAssignModalOpen, assignmentSession?.session_id, assignmentSession?.status]);

  // ── Open RFID Assignment Dialog ──
  function handleOpenRfidModal(student: StudentRecord) {
    setSelectedStudentForRfid(student);
    setAssignmentSession(null);
    setAssignmentError(null);
    setAssignmentSuccess(null);
    setAssignmentReason("");
    setAssignmentTimeoutSec(60);
    setCountdown(60);
    setIsAssignModalOpen(true);
  }

  // ── Initiate Hardware Scan Mode on ESP8266 Reader ──
  async function handleStartAssignment() {
    if (!selectedStudentForRfid) return;
    setAssignmentLoading(true);
    setAssignmentError(null);
    setAssignmentSuccess(null);

    const isReplacement = Boolean(
      selectedStudentForRfid.rfid_uid &&
      !selectedStudentForRfid.rfid_uid.startsWith("DEACTIVATED") &&
      !selectedStudentForRfid.rfid_uid.startsWith("PENDING")
    );

    try {
      const session = await rfidService.startAssignment({
        student_id: selectedStudentForRfid.id,
        mode: isReplacement ? "REPLACE" : "ASSIGN",
        device_id: selectedReader,
        timeout_seconds: assignmentTimeoutSec,
      });
      setAssignmentSession(session);
      setCountdown(session.expires_in_seconds || assignmentTimeoutSec);
    } catch (err: unknown) {
      setAssignmentError(err instanceof ApiError ? err.message : "Failed to initiate card assignment on hardware reader.");
    } finally {
      setAssignmentLoading(false);
    }
  }

  // ── Cancel Ongoing Session ──
  async function handleCancelAssignment() {
    if (assignmentSession?.session_id && assignmentSession.status === "PENDING_SCAN") {
      try {
        await rfidService.cancelAssignment(assignmentSession.session_id);
      } catch {
        // Silent
      }
    }
    setAssignmentSession((prev: RfidAssignmentSession | null) => (prev ? { ...prev, status: "CANCELLED" } : null));
  }

  // ── Confirm Scanned UID Association ──
  async function handleConfirmAssignment() {
    if (!assignmentSession || !selectedStudentForRfid || !assignmentSession.scanned_uid) return;
    setAssignmentLoading(true);
    setAssignmentError(null);

    try {
      const res = await rfidService.confirmAssignment({
        session_id: assignmentSession.session_id,
        student_id: selectedStudentForRfid.id,
        rfid_uid: assignmentSession.scanned_uid,
        reason: assignmentReason.trim() || undefined,
      });

      setAssignmentSuccess(
        `Physical card UID ${res.rfid_uid} successfully bound to ${res.student_name} (${res.roll_no}).`
      );
      loadData();
    } catch (err: unknown) {
      setAssignmentError(
        err instanceof ApiError ? err.message : "Failed to confirm card assignment. Backend rejected the request."
      );
    } finally {
      setAssignmentLoading(false);
    }
  }

  // ── Deactivate Student RFID Card ──
  async function handleConfirmDeactivateCard() {
    if (!deactivatingCardStudent) return;
    setDeactivateCardLoading(true);
    try {
      const res = await rfidService.deactivateCard({
        student_id: deactivatingCardStudent.id,
        reason: deactivateReason.trim() || undefined,
      });
      setActionMessage(
        `RFID card (${res.deactivated_rfid_uid}) for student ${res.student_name} was successfully deactivated.`
      );
      setDeactivatingCardStudent(null);
      setDeactivateReason("");
      loadData();
    } catch (err: unknown) {
      alert(err instanceof ApiError ? err.message : "Failed to deactivate student RFID card.");
    } finally {
      setDeactivateCardLoading(false);
    }
  }

  function handleOpenModal(student?: StudentRecord) {
    if (student) {
      setEditingStudent(student);
      setFormRoll(student.roll_no || student.roll_number || "");
      setFormName(student.name || student.full_name || "");
      setFormEmail(student.email || "");
      setFormDepartment(student.department || "Computer Science & Engineering");
      setFormYear(student.year || "3rd Year");
      setFormDivision(student.division || student.division_name || "A");
      setFormRfid(student.rfid_uid || "");
    } else {
      setEditingStudent(null);
      setFormRoll("");
      setFormName("");
      setFormEmail("");
      setFormDepartment("Computer Science & Engineering");
      setFormYear("3rd Year");
      setFormDivision(divisions[0]?.name || "A");
      setFormRfid("");
    }
    setIsModalOpen(true);
  }

  async function handleSaveStudent(e: FormEvent) {
    e.preventDefault();
    if (submitting) return;

    setSubmitting(true);
    setActionMessage(null);

    const payload = {
      name: formName.trim(),
      roll_no: formRoll.trim(),
      department: formDepartment.trim() || "Computer Science & Engineering",
      year: formYear.trim() || "3rd Year",
      division: formDivision.trim() || "A",
      email: formEmail.trim() || undefined,
      rfid_uid: formRfid.trim() || undefined,
      full_name: formName.trim(),
      roll_number: formRoll.trim(),
      division_name: formDivision.trim() || "A",
    };

    try {
      if (editingStudent) {
        await studentService.update(editingStudent.id, payload);
        setActionMessage("Student record updated successfully.");
      } else {
        await studentService.create(payload);
        setActionMessage("New student enrolled successfully.");
      }
      setIsModalOpen(false);
      loadData();
    } catch (err: unknown) {
      alert(err instanceof ApiError ? err.message : "Failed to save student. Ensure backend /students endpoint is online.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeactivate(id: string | number) {
    try {
      await studentService.deactivate(id);
      setDeactivatingId(null);
      loadData();
    } catch (err: unknown) {
      alert(err instanceof ApiError ? err.message : "Unable to deactivate student.");
    }
  }

  function exportCSV() {
    if (students.length === 0) {
      alert("No student records available to export.");
      return;
    }
    const headers = ["Roll No", "Full Name", "Department", "Academic Year", "Division", "Email", "RFID UID", "Face Status", "Account Status"];
    const rows = students.map((s) => [
      s.roll_no || s.roll_number,
      `"${s.name || s.full_name}"`,
      `"${s.department || "Computer Science"}"`,
      `"${s.year || "3rd Year"}"`,
      `"${s.division || s.division_name || "A"}"`,
      s.email || "",
      s.rfid_uid || "",
      s.face_enrolled ? "Enrolled" : "Pending",
      s.is_active ? "Active" : "Inactive",
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `smartattend_students_${new Date().toISOString().split("T")[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  const filteredStudents = students.filter((s) => {
    if (selectedDivision) {
      const matchDiv =
        s.division === selectedDivision ||
        s.division_name === selectedDivision ||
        String(s.division_id) === selectedDivision;
      if (!matchDiv) return false;
    }
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const nameMatch = (s.name || s.full_name || "").toLowerCase().includes(q);
    const rollMatch = (s.roll_no || s.roll_number || "").toLowerCase().includes(q);
    const emailMatch = (s.email || "").toLowerCase().includes(q);
    const deptMatch = (s.department || "").toLowerCase().includes(q);
    const rfidMatch = (s.rfid_uid || "").toLowerCase().includes(q);
    return nameMatch || rollMatch || emailMatch || deptMatch || rfidMatch;
  });

  return (
    <ProtectedPage requiredRole="admin">
      <DashboardLayout
        role="admin"
        title="Student Directory"
        subtitle="Manage enrolled students, academic divisions, and assigned RFID card tags."
        breadcrumbs={[{ label: "Students" }]}
        actions={
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={exportCSV}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#17171B] hover:bg-[#1F1F24] border border-[#2A2A30] text-xs font-semibold text-[#F5F5F5] transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export CSV</span>
            </button>
            <button
              type="button"
              onClick={() => handleOpenModal()}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-[0_0_15px_rgba(255,215,0,0.2)] transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Student</span>
            </button>
          </div>
        }
      >
        {/* Success / Info Toast */}
        {actionMessage && (
          <div className="mb-6 p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/60 text-[#7BD88F] text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{actionMessage}</span>
            </div>
            <button type="button" onClick={() => setActionMessage(null)}>
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Search & Filter Toolbar */}
        <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-4 mb-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-[#A1A1AA] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name, roll, or email..."
              className="w-full h-10 pl-10 pr-4 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/50 focus:border-[#FFD700] focus:outline-none transition-colors"
            />
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <select
              value={selectedDivision}
              onChange={(e) => setSelectedDivision(e.target.value)}
              className="h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none transition-colors"
            >
              <option value="">All Divisions</option>
              {divisions.map((d) => (
                <option key={d.id} value={d.name}>
                  Division {d.name} ({d.code || `DIV-${d.name}`})
                </option>
              ))}
            </select>

            <button
              type="button"
              onClick={loadData}
              disabled={loading}
              className="p-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors"
              title="Refresh student records"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-[#FFD700]" : ""}`} />
            </button>
          </div>
        </div>

        {/* Student Records Table or Honest Empty State */}
        {loading ? (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-12 text-center text-xs text-[#A1A1AA]">
            <RefreshCw className="w-6 h-6 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Loading authorized student records from database...</span>
          </div>
        ) : error ? (
          <EmptyState
            icon={AlertCircle}
            title="Database Connection Notice"
            description={`${error} In accordance with the No-Dummy-Data policy, no simulated students are displayed.`}
            action={
              <button
                type="button"
                onClick={loadData}
                className="px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
              >
                Retry Request
              </button>
            }
          />
        ) : filteredStudents.length === 0 ? (
          <EmptyState
            icon={GraduationCap}
            title="No Student Records Enrolled"
            description={
              searchQuery
                ? `No students matching "${searchQuery}" were found.`
                : "The institutional database currently has no students enrolled for this filter. Click 'Add Student' above to enroll your first student record."
            }
            action={
              <button
                type="button"
                onClick={() => handleOpenModal()}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs shadow-md"
              >
                <Plus className="w-4 h-4" />
                <span>Enroll New Student</span>
              </button>
            }
          />
        ) : (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-[#17171B] text-[#A1A1AA] border-b border-[#2A2A30]">
                    <th className="py-3.5 px-4 font-semibold">Roll No</th>
                    <th className="py-3.5 px-4 font-semibold">Full Name</th>
                    <th className="py-3.5 px-4 font-semibold">Department & Year</th>
                    <th className="py-3.5 px-4 font-semibold">Division</th>
                    <th className="py-3.5 px-4 font-semibold">Email</th>
                    <th className="py-3.5 px-4 font-semibold">RFID Card Tag</th>
                    <th className="py-3.5 px-4 font-semibold">Face Status</th>
                    <th className="py-3.5 px-4 font-semibold">Status</th>
                    <th className="py-3.5 px-4 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2A2A30]/50 text-[#F5F5F5]">
                  {filteredStudents.map((student) => {
                    const roll = student.roll_no || student.roll_number || "—";
                    const name = student.name || student.full_name || "—";
                    const div = student.division || student.division_name || "A";
                    const hasActiveCard = Boolean(
                      student.rfid_uid &&
                      !student.rfid_uid.startsWith("DEACTIVATED") &&
                      !student.rfid_uid.startsWith("PENDING")
                    );
                    const isDeactivated = Boolean(student.rfid_uid?.startsWith("DEACTIVATED"));

                    return (
                      <tr key={student.id} className="hover:bg-[#17171B]/50 transition-colors">
                        <td className="py-3.5 px-4 font-bold text-[#FFD700]">{roll}</td>
                        <td className="py-3.5 px-4 font-medium">{name}</td>
                        <td className="py-3.5 px-4 text-[#A1A1AA]">
                          <div className="font-medium text-[#F5F5F5]">{student.department || "Computer Science"}</div>
                          <div className="text-[11px] text-[#A1A1AA]/80">{student.year || "3rd Year"}</div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="px-2.5 py-1 rounded-lg bg-[#17171B] border border-[#2A2A30] font-semibold text-[#FFD700]">
                            Div {div}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-[#A1A1AA]">{student.email || "—"}</td>
                        <td className="py-3.5 px-4 font-mono text-[11px]">
                          {hasActiveCard ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-950/40 border border-emerald-800/50 text-[#7BD88F] font-semibold">
                              <CreditCard className="w-3.5 h-3.5 text-emerald-400" />
                              <span>{student.rfid_uid}</span>
                            </span>
                          ) : isDeactivated ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-950/30 border border-red-800/40 text-red-400 text-[10px]">
                              <Ban className="w-3 h-3" />
                              <span>Card Deactivated</span>
                            </span>
                          ) : (
                            <span className="text-zinc-500 italic">Unassigned</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          {student.face_enrolled ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-950/40 border border-emerald-800/50 text-[#7BD88F] text-[11px] font-semibold">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                              <span>Enrolled</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-950/30 border border-amber-800/40 text-amber-400 text-[11px] font-semibold">
                              <Clock className="w-3.5 h-3.5 text-amber-400" />
                              <span>Pending</span>
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          <StatusBadge
                            status={student.is_active ? "verified" : "offline"}
                            labelOverride={student.is_active ? "Active" : "Inactive"}
                          />
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {/* Assign / Replace RFID Action Button */}
                            <button
                              type="button"
                              onClick={() => handleOpenRfidModal(student)}
                              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${
                                hasActiveCard
                                  ? "bg-[#17171B] hover:bg-[#1F1F24] border-[#2A2A30] text-[#A1A1AA] hover:text-[#FFD700] hover:border-[#FFD700]/30"
                                  : "bg-[#FFD700]/10 hover:bg-[#FFD700]/20 border-[#FFD700]/30 text-[#FFD700]"
                              }`}
                              title={hasActiveCard ? "Replace Assigned RFID Card" : "Assign RFID Card from Hardware Reader"}
                            >
                              <CreditCard className="w-3.5 h-3.5" />
                              <span>{hasActiveCard ? "Replace" : "Assign RFID"}</span>
                            </button>

                            {/* Deactivate Card Button (Only for students with active cards) */}
                            {hasActiveCard && (
                              <button
                                type="button"
                                onClick={() => {
                                  setDeactivatingCardStudent(student);
                                  setDeactivateReason("");
                                }}
                                className="p-1.5 rounded-lg bg-[#17171B] border border-[#2A2A30] text-[#A1A1AA] hover:text-amber-400 hover:border-amber-500/30 transition-colors"
                                title="Deactivate / Revoke RFID Card"
                              >
                                <ShieldAlert className="w-3.5 h-3.5" />
                              </button>
                            )}

                            {/* Edit Student Record */}
                            <button
                              type="button"
                              onClick={() => handleOpenModal(student)}
                              className="p-1.5 rounded-lg bg-[#17171B] border border-[#2A2A30] text-[#A1A1AA] hover:text-[#FFD700] hover:border-[#FFD700]/30 transition-colors"
                              title="Edit Student"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </button>

                            {/* Deactivate Student Profile */}
                            <button
                              type="button"
                              onClick={() => setDeactivatingId(student.id)}
                              className="p-1.5 rounded-lg bg-[#17171B] border border-[#2A2A30] text-[#A1A1AA] hover:text-red-400 hover:border-red-500/30 transition-colors"
                              title="Deactivate Student Account"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="p-4 border-t border-[#2A2A30] flex items-center justify-between text-[11px] text-[#A1A1AA]">
              <span>Showing {filteredStudents.length} authorized student records</span>
              <span>Hardware-backed RFID associations via ESP8266 + RC522</span>
            </div>
          </div>
        )}

        {/* ── RFID CARD ASSIGNMENT MODAL ── */}
        {isAssignModalOpen && selectedStudentForRfid && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
              className="fixed inset-0 bg-black/80 backdrop-blur-sm"
              onClick={() => {
                if (assignmentSession?.status === "PENDING_SCAN") {
                  handleCancelAssignment();
                }
                setIsAssignModalOpen(false);
              }}
            />
            <div className="relative w-full max-w-lg bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-8 shadow-2xl z-10 animate-in fade-in zoom-in-95 duration-150">
              {/* Modal Header */}
              <div className="flex items-start justify-between pb-4 border-b border-[#2A2A30] mb-5">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-[#FFD700]/10 border border-[#FFD700]/20 text-[#FFD700] flex items-center justify-center">
                    <CreditCard className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-[#F5F5F5]">
                      {selectedStudentForRfid.rfid_uid && !selectedStudentForRfid.rfid_uid.startsWith("DEACTIVATED")
                        ? "Replace RFID Card"
                        : "Assign RFID Card"}
                    </h3>
                    <p className="text-xs text-[#A1A1AA]">
                      Pair real physical card UID captured from ESP8266 reader
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    if (assignmentSession?.status === "PENDING_SCAN") {
                      handleCancelAssignment();
                    }
                    setIsAssignModalOpen(false);
                  }}
                  className="p-1.5 rounded-xl text-[#A1A1AA] hover:text-[#F5F5F5]"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Student Target Context Card */}
              <div className="p-4 rounded-2xl bg-[#17171B] border border-[#2A2A30] mb-5">
                <div className="flex items-center justify-between text-xs">
                  <div>
                    <span className="text-[#A1A1AA]">Student: </span>
                    <strong className="text-[#F5F5F5]">{selectedStudentForRfid.name || selectedStudentForRfid.full_name}</strong>
                    <span className="text-[#FFD700] ml-2 font-mono">({selectedStudentForRfid.roll_no || selectedStudentForRfid.roll_number})</span>
                  </div>
                  <span className="text-[11px] px-2 py-0.5 rounded-md bg-[#111114] border border-[#2A2A30] text-[#A1A1AA]">
                    Division {selectedStudentForRfid.division || selectedStudentForRfid.division_name || "A"}
                  </span>
                </div>
                {selectedStudentForRfid.rfid_uid && !selectedStudentForRfid.rfid_uid.startsWith("DEACTIVATED") && (
                  <div className="mt-2 pt-2 border-t border-[#2A2A30]/60 flex items-center justify-between text-[11px]">
                    <span className="text-[#A1A1AA]">Current Assigned Card:</span>
                    <code className="text-amber-400 font-mono font-semibold">{selectedStudentForRfid.rfid_uid}</code>
                  </div>
                )}
              </div>

              {/* Error Notice Display */}
              {assignmentError && (
                <div className="mb-5 p-3.5 rounded-2xl bg-red-950/40 border border-red-800/60 text-red-300 text-xs flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-semibold">Assignment Warning</p>
                    <p className="text-[11px] mt-0.5 leading-relaxed text-red-300/90">{assignmentError}</p>
                  </div>
                </div>
              )}

              {/* Success Screen */}
              {assignmentSuccess ? (
                <div className="text-center py-6">
                  <div className="w-14 h-14 rounded-full bg-emerald-950/40 border border-emerald-800/60 text-[#7BD88F] flex items-center justify-center mx-auto mb-3">
                    <Check className="w-7 h-7" />
                  </div>
                  <h4 className="text-base font-bold text-[#F5F5F5]">Card Association Complete!</h4>
                  <p className="text-xs text-[#A1A1AA] mt-1.5 mb-6 max-w-sm mx-auto leading-relaxed">
                    {assignmentSuccess}
                  </p>
                  <button
                    type="button"
                    onClick={() => setIsAssignModalOpen(false)}
                    className="w-full py-2.5 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs transition-colors"
                  >
                    Done & Close
                  </button>
                </div>
              ) : assignmentSession?.status === "SCANNED" ? (
                /* ── STATE 3: CARD SCANNED BY HARDWARE READER ── */
                <div className="space-y-4">
                  <div className="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-800/40 text-center">
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-900/40 text-emerald-300 text-[10px] font-semibold mb-2">
                      <Radio className="w-3 h-3 animate-pulse" />
                      <span>Physical Card Detected</span>
                    </div>
                    <p className="text-xs text-[#A1A1AA]">Scanned RFID Card UID</p>
                    <p className="text-2xl font-mono font-extrabold text-[#7BD88F] tracking-wider mt-1 mb-1">
                      {assignmentSession.scanned_uid}
                    </p>
                    <p className="text-[10px] text-[#A1A1AA]">
                      Captured via reader: <code className="text-[#F5F5F5]">{assignmentSession.device_id || selectedReader}</code>
                    </p>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                      Administrative Reason / Notes (Audit Trail)
                    </label>
                    <input
                      type="text"
                      value={assignmentReason}
                      onChange={(e) => setAssignmentReason(e.target.value)}
                      placeholder="e.g. Initial institutional smart card issuance"
                      className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/50 focus:border-[#FFD700] focus:outline-none"
                    />
                    <span className="text-[10px] text-[#A1A1AA] mt-1 block">
                      This action will be permanently logged in the Supabase audit security log.
                    </span>
                  </div>

                  <div className="pt-2 flex items-center justify-end gap-3">
                    <button
                      type="button"
                      onClick={() => handleStartAssignment()}
                      className="px-4 py-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA] hover:text-[#F5F5F5] inline-flex items-center gap-1.5"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Rescan Card</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleConfirmAssignment}
                      disabled={assignmentLoading}
                      className="px-6 py-2.5 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md transition-all disabled:opacity-50 inline-flex items-center gap-1.5"
                    >
                      {assignmentLoading ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Verifying & Saving...</span>
                        </>
                      ) : (
                        <>
                          <ShieldCheck className="w-4 h-4" />
                          <span>Confirm Card Association</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ) : assignmentSession?.status === "PENDING_SCAN" ? (
                /* ── STATE 2: PENDING PHYSICAL SCAN ON HARDWARE READER ── */
                <div className="text-center py-5 space-y-4">
                  {/* Radar Pulse Animation */}
                  <div className="relative w-24 h-24 mx-auto flex items-center justify-center">
                    <div className="absolute inset-0 rounded-full bg-[#FFD700]/10 animate-ping" />
                    <div className="absolute inset-2 rounded-full bg-[#FFD700]/20 animate-pulse" />
                    <div className="relative w-16 h-16 rounded-full bg-[#17171B] border-2 border-[#FFD700] text-[#FFD700] flex items-center justify-center shadow-[0_0_20px_rgba(255,215,0,0.3)]">
                      <Radio className="w-7 h-7 animate-pulse" />
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-[#F5F5F5]">Awaiting Physical Card Tap</h4>
                    <p className="text-xs text-[#A1A1AA] mt-1 max-w-xs mx-auto leading-relaxed">
                      Please hold student's physical RFID badge near reader terminal{" "}
                      <code className="text-[#FFD700] font-semibold">{selectedReader}</code>.
                    </p>
                  </div>

                  {/* Countdown Timer */}
                  <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#17171B] border border-[#2A2A30] text-xs font-mono">
                    <Clock className="w-3.5 h-3.5 text-[#FFD700]" />
                    <span className="text-[#F5F5F5] font-semibold">{countdown}s remaining</span>
                  </div>

                  {/* Anti-attendance guarantee banner */}
                  <div className="p-3 rounded-xl bg-blue-950/20 border border-blue-800/40 text-blue-300 text-[11px] text-left flex items-start gap-2">
                    <ShieldCheck className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                    <span>
                      <strong>Mode Separation Active:</strong> Tapping a card right now will capture the UID for student assignment only. Attendance will <strong>not</strong> be marked.
                    </span>
                  </div>

                  <div className="pt-2 flex items-center justify-center gap-3">
                    <button
                      type="button"
                      onClick={handleCancelAssignment}
                      className="px-5 py-2.5 rounded-xl bg-[#17171B] hover:bg-[#1F1F24] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA] hover:text-[#F5F5F5]"
                    >
                      Cancel Scan Mode
                    </button>
                  </div>
                </div>
              ) : assignmentSession?.status === "EXPIRED" ? (
                /* ── STATE: SESSION TIMED OUT ── */
                <div className="text-center py-6 space-y-4">
                  <div className="w-12 h-12 rounded-full bg-amber-950/40 border border-amber-800/60 text-amber-400 flex items-center justify-center mx-auto">
                    <Clock className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-[#F5F5F5]">Assignment Session Timed Out</h4>
                    <p className="text-xs text-[#A1A1AA] mt-1 max-w-xs mx-auto">
                      No physical RFID card was tapped on reader <code className="text-[#FFD700]">{selectedReader}</code> before the timeout window expired.
                    </p>
                  </div>
                  <div className="flex items-center justify-center gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setIsAssignModalOpen(false)}
                      className="px-4 py-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA]"
                    >
                      Close
                    </button>
                    <button
                      type="button"
                      onClick={handleStartAssignment}
                      className="px-5 py-2.5 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs inline-flex items-center gap-1.5"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Retry Card Scan</span>
                    </button>
                  </div>
                </div>
              ) : (
                /* ── STATE 1: READY TO INITIATE ASSIGNMENT MODE ── */
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                        Target Hardware Gateway
                      </label>
                      <select
                        value={selectedReader}
                        onChange={(e) => setSelectedReader(e.target.value)}
                        className="w-full h-10 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                      >
                        {devices.length > 0 ? (
                          devices.map((d) => (
                            <option key={d.device_id} value={d.device_id}>
                              {d.device_name} ({d.device_id})
                            </option>
                          ))
                        ) : (
                          <>
                            <option value="GATE-READER-01">Campus Main Gate (GATE-READER-01)</option>
                            <option value="LAB-READER-01">AIoT Lab Ingress (LAB-READER-01)</option>
                          </>
                        )}
                      </select>
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                        Scan Timeout Window
                      </label>
                      <select
                        value={assignmentTimeoutSec}
                        onChange={(e) => setAssignmentTimeoutSec(Number(e.target.value))}
                        className="w-full h-10 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                      >
                        <option value={30}>30 Seconds</option>
                        <option value={60}>60 Seconds (Recommended)</option>
                        <option value={120}>120 Seconds</option>
                      </select>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-[#17171B]/70 border border-[#2A2A30] text-xs text-[#A1A1AA] leading-relaxed">
                    <p className="font-semibold text-[#F5F5F5] mb-1">How it works:</p>
                    <ol className="list-decimal pl-4 space-y-1 text-[11px]">
                      <li>Initiating assignment arms the selected ESP8266 reader for card capture.</li>
                      <li>Hold the student badge to the reader within the countdown window.</li>
                      <li>Review the verified physical UID and confirm the database binding.</li>
                    </ol>
                  </div>

                  <div className="pt-2 flex items-center justify-end gap-3">
                    <button
                      type="button"
                      onClick={() => setIsAssignModalOpen(false)}
                      className="px-4 py-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA] hover:text-[#F5F5F5]"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleStartAssignment}
                      disabled={assignmentLoading}
                      className="px-6 py-2.5 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md transition-all inline-flex items-center gap-2 disabled:opacity-50"
                    >
                      {assignmentLoading ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Initiating Reader...</span>
                        </>
                      ) : (
                        <>
                          <Radio className="w-3.5 h-3.5" />
                          <span>Initiate Card Assignment Mode</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── DEACTIVATE CARD CONFIRMATION MODAL ── */}
        {deactivatingCardStudent && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
              className="fixed inset-0 bg-black/80 backdrop-blur-sm"
              onClick={() => setDeactivatingCardStudent(null)}
            />
            <div className="relative w-full max-w-sm bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 shadow-2xl z-10 text-center animate-in fade-in zoom-in-95 duration-150">
              <div className="w-12 h-12 rounded-full bg-amber-950/40 border border-amber-800/60 text-amber-400 flex items-center justify-center mx-auto mb-4">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-[#F5F5F5]">Deactivate Student RFID Card?</h3>
              <p className="text-xs text-[#A1A1AA] mt-1.5 mb-4 leading-relaxed">
                Revoke card UID <code className="text-amber-400 font-mono font-semibold">{deactivatingCardStudent.rfid_uid}</code> for student{" "}
                <strong className="text-[#F5F5F5]">{deactivatingCardStudent.name || deactivatingCardStudent.full_name}</strong>?
              </p>

              <div className="text-left mb-5">
                <label className="text-[11px] font-semibold text-[#A1A1AA] block mb-1">
                  Reason for Deactivation *
                </label>
                <input
                  type="text"
                  value={deactivateReason}
                  onChange={(e) => setDeactivateReason(e.target.value)}
                  placeholder="e.g. Card reported lost or damaged"
                  className="w-full h-9 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/50 focus:border-amber-400 focus:outline-none"
                />
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setDeactivatingCardStudent(null)}
                  className="flex-1 py-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA]"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmDeactivateCard}
                  disabled={deactivateCardLoading}
                  className="flex-1 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-[#0B0B0D] font-bold text-xs transition-colors disabled:opacity-50"
                >
                  {deactivateCardLoading ? "Revoking..." : "Deactivate Card"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── CREATE / EDIT STUDENT MODAL DIALOG ── */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
              className="fixed inset-0 bg-black/80 backdrop-blur-sm"
              onClick={() => setIsModalOpen(false)}
            />
            <div className="relative w-full max-w-lg bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-8 shadow-2xl z-10 animate-in fade-in zoom-in-95 duration-150">
              <div className="flex items-center justify-between pb-5 border-b border-[#2A2A30] mb-6">
                <div>
                  <h3 className="text-lg font-bold text-[#F5F5F5]">
                    {editingStudent ? "Edit Student Record" : "Enroll New Student"}
                  </h3>
                  <p className="text-xs text-[#A1A1AA] mt-0.5">
                    Enter official institutional details. Fields will be validated by FastAPI.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="p-1.5 rounded-xl text-[#A1A1AA] hover:text-[#F5F5F5]"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSaveStudent} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                      Roll Number *
                    </label>
                    <input
                      type="text"
                      required
                      value={formRoll}
                      onChange={(e) => setFormRoll(e.target.value)}
                      placeholder="e.g. 2024-AIML-01"
                      className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                      Division Cohort *
                    </label>
                    <select
                      value={formDivision}
                      onChange={(e) => setFormDivision(e.target.value)}
                      className="w-full h-10 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                    >
                      {divisions.map((d) => (
                        <option key={d.id} value={d.name}>
                          Division {d.name} ({d.code || `DIV-${d.name}`})
                        </option>
                      ))}
                      {!divisions.some((d) => d.name === "A") && <option value="A">Division A</option>}
                      {!divisions.some((d) => d.name === "B") && <option value="B">Division B</option>}
                      {!divisions.some((d) => d.name === "C") && <option value="C">Division C</option>}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder="e.g. Priya Sharma"
                    className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                      Department *
                    </label>
                    <input
                      type="text"
                      required
                      value={formDepartment}
                      onChange={(e) => setFormDepartment(e.target.value)}
                      placeholder="e.g. Computer Science & Engineering"
                      className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                      Academic Year *
                    </label>
                    <select
                      value={formYear}
                      onChange={(e) => setFormYear(e.target.value)}
                      className="w-full h-10 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                    >
                      <option value="1st Year">1st Year (FE)</option>
                      <option value="2nd Year">2nd Year (SE)</option>
                      <option value="3rd Year">3rd Year (TE)</option>
                      <option value="4th Year">4th Year (BE / Final)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                    Institutional Email
                  </label>
                  <input
                    type="email"
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                    placeholder="student@institution.edu"
                    className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                    RFID Card UID (Optional)
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={formRfid}
                      onChange={(e) => setFormRfid(e.target.value)}
                      placeholder="e.g. 5A:3F:82:1C"
                      className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] font-mono focus:border-[#FFD700] focus:outline-none"
                    />
                    <CreditCard className="w-4 h-4 text-[#A1A1AA] absolute right-3.5 top-1/2 -translate-y-1/2" />
                  </div>
                  <span className="text-[10px] text-[#A1A1AA] mt-1 block">
                    Optional. Use the &apos;Assign RFID&apos; action button on the table for live hardware reader pairing.
                  </span>
                </div>

                <div className="pt-4 flex items-center justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA] hover:text-[#F5F5F5]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-6 py-2.5 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs shadow-md transition-all disabled:opacity-50"
                  >
                    {submitting ? "Saving..." : editingStudent ? "Save Changes" : "Enroll Student"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ── DEACTIVATE STUDENT ACCOUNT CONFIRMATION MODAL ── */}
        {deactivatingId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setDeactivatingId(null)} />
            <div className="relative w-full max-w-sm bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 shadow-2xl z-10 text-center">
              <div className="w-12 h-12 rounded-full bg-red-950/40 border border-red-800/60 text-red-400 flex items-center justify-center mx-auto mb-4">
                <Trash2 className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-[#F5F5F5]">Deactivate Student?</h3>
              <p className="text-xs text-[#A1A1AA] mt-2 mb-6 leading-relaxed">
                This will revoke attendance tracking and kiosk check-in access for this student account.
              </p>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setDeactivatingId(null)}
                  className="flex-1 py-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA]"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleDeactivate(deactivatingId)}
                  className="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold text-xs"
                >
                  Deactivate
                </button>
              </div>
            </div>
          </div>
        )}
      </DashboardLayout>
    </ProtectedPage>
  );
}
