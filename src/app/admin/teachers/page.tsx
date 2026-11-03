"use client";

import React, { useState, useEffect, type FormEvent } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { teacherService, classService, TeacherRecord, ClassDivisionRecord } from "@/lib/services";
import { ApiError } from "@/lib/api";
import {
  Users,
  Plus,
  Search,
  Download,
  Trash2,
  Edit2,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  X,
  ChevronDown,
  Check,
  Layers
} from "lucide-react";

export default function TeacherManagementPage() {
  const [teachers, setTeachers] = useState<TeacherRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDept, setSelectedDept] = useState("");

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTeacher, setEditingTeacher] = useState<TeacherRecord | null>(null);
  const [formEmpId, setFormEmpId] = useState("");
  const [formName, setFormName] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formDept, setFormDept] = useState("Computer Science & Engineering");
  const [formDivisions, setFormDivisions] = useState("");
  const [divisionsList, setDivisionsList] = useState<ClassDivisionRecord[]>([]);
  const [selectedDivisions, setSelectedDivisions] = useState<string[]>([]);
  const [isDivDropdownOpen, setIsDivDropdownOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [deactivatingId, setDeactivatingId] = useState<string | number | null>(null);

  async function loadTeachers() {
    setLoading(true);
    setError(null);
    try {
      const data = await teacherService.getAll({
        department: selectedDept || undefined,
        query: searchQuery || undefined,
      });
      setTeachers(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to connect to FastAPI /teachers endpoint.");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTeachers();
  }, [selectedDept]);

  useEffect(() => {
    async function loadDivisions() {
      try {
        const classes = await classService.getAll();
        setDivisionsList(classes || []);
      } catch (err) {
        console.warn("Unable to fetch divisions for dropdown:", err);
      }
    }
    loadDivisions();
  }, []);

  function handleOpenModal(teacher?: TeacherRecord) {
    if (teacher) {
      setEditingTeacher(teacher);
      setFormEmpId(teacher.employee_id || teacher.teacher_id || "");
      setFormName(teacher.full_name || teacher.name || "");
      setFormEmail(teacher.email || "");
      setFormDept(teacher.department || "Computer Science & Engineering");
      const currentDivs = teacher.assigned_divisions || [];
      setSelectedDivisions(currentDivs);
      setFormDivisions(currentDivs.join(", "));
    } else {
      setEditingTeacher(null);
      setFormEmpId("");
      setFormName("");
      setFormEmail("");
      setFormDept("Computer Science & Engineering");
      setSelectedDivisions([]);
      setFormDivisions("");
    }
    setIsDivDropdownOpen(false);
    setIsModalOpen(true);
  }

  function toggleDivision(divName: string) {
    setSelectedDivisions((prev) => {
      const exists = prev.includes(divName);
      const updated = exists ? prev.filter((d) => d !== divName) : [...prev, divName];
      setFormDivisions(updated.join(", "));
      return updated;
    });
  }

  function selectAllDivisions() {
    const all = divisionsList.map((d) => d.name);
    setSelectedDivisions(all);
    setFormDivisions(all.join(", "));
  }

  function clearAllDivisions() {
    setSelectedDivisions([]);
    setFormDivisions("");
  }

  function handleManualDivisionsChange(val: string) {
    setFormDivisions(val);
    const parsed = val.split(",").map((s) => s.trim()).filter(Boolean);
    setSelectedDivisions(parsed);
  }

  async function handleSaveTeacher(e: FormEvent) {
    e.preventDefault();
    if (submitting) return;

    setSubmitting(true);
    setActionMessage(null);

    const finalDivs = selectedDivisions.length > 0
      ? selectedDivisions
      : formDivisions.split(",").map((s) => s.trim()).filter(Boolean);

    const payload = {
      employee_id: formEmpId.trim(),
      teacher_id: formEmpId.trim(),
      full_name: formName.trim(),
      name: formName.trim(),
      email: formEmail.trim(),
      department: formDept,
      assigned_divisions: finalDivs,
    };

    try {
      if (editingTeacher) {
        await teacherService.update(editingTeacher.id, payload);
        setActionMessage("Faculty record updated successfully.");
      } else {
        await teacherService.create(payload);
        setActionMessage("New faculty profile onboarded.");
      }
      setIsModalOpen(false);
      loadTeachers();
    } catch (err: unknown) {
      alert(err instanceof ApiError ? err.message : "Failed to save faculty record.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeactivate(id: string | number) {
    try {
      await teacherService.deactivate(id);
      setDeactivatingId(null);
      loadTeachers();
    } catch (err: unknown) {
      alert(err instanceof ApiError ? err.message : "Unable to deactivate faculty profile.");
    }
  }

  function exportCSV() {
    if (teachers.length === 0) {
      alert("No faculty records available to export.");
      return;
    }
    const headers = ["ID", "Employee ID", "Full Name", "Email", "Department", "Divisions", "Status"];
    const rows = teachers.map((t) => [
      t.id,
      t.employee_id || t.teacher_id,
      `"${t.full_name || t.name}"`,
      t.email,
      `"${t.department}"`,
      `"${(t.assigned_divisions || []).join("; ")}"`,
      t.is_active ? "Active" : "Inactive",
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `smartattend_faculty_${new Date().toISOString().split("T")[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  const filtered = teachers.filter((t) => {
    const q = searchQuery.toLowerCase();
    const name = (t.full_name || t.name || "").toLowerCase();
    const empId = (t.employee_id || t.teacher_id || "").toLowerCase();
    const email = (t.email || "").toLowerCase();
    const dept = (t.department || "").toLowerCase();
    return name.includes(q) || empId.includes(q) || email.includes(q) || dept.includes(q);
  });

  return (
    <ProtectedPage requiredRole="admin">
      <DashboardLayout
        role="admin"
        title="Faculty Management"
        subtitle="Maintain faculty accounts, departmental roles, and assigned division teaching registers."
        breadcrumbs={[{ label: "Faculty" }]}
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
              <span>Add Faculty</span>
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

        <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-4 mb-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-[#A1A1AA] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search faculty by name or ID..."
              className="w-full h-10 pl-10 pr-4 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/50 focus:border-[#FFD700] focus:outline-none transition-colors"
            />
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none transition-colors"
            >
              <option value="">All Departments</option>
              <option value="Computer Science & Engineering">Computer Science & Eng</option>
              <option value="Artificial Intelligence & Machine Learning">AI & Machine Learning</option>
              <option value="Information Technology">Information Technology</option>
              <option value="Electronics & Telecommunication">Electronics & Telecom</option>
            </select>

            <button
              type="button"
              onClick={loadTeachers}
              disabled={loading}
              className="p-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors"
              title="Refresh faculty"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-[#FFD700]" : ""}`} />
            </button>
          </div>
        </div>

        {loading ? (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl p-12 text-center text-xs text-[#A1A1AA]">
            <RefreshCw className="w-6 h-6 animate-spin text-[#FFD700] mx-auto mb-2" />
            <span>Loading authorized faculty records...</span>
          </div>
        ) : error ? (
          <EmptyState
            icon={AlertCircle}
            title="Database Connection Notice"
            description={`${error} No mock faculty records are generated.`}
            action={
              <button
                type="button"
                onClick={loadTeachers}
                className="px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
              >
                Retry
              </button>
            }
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No Faculty Records Found"
            description={
              searchQuery
                ? `No faculty matching "${searchQuery}" was found.`
                : "The institutional database currently has no faculty registered. Click 'Add Faculty' above to create a profile."
            }
            action={
              <button
                type="button"
                onClick={() => handleOpenModal()}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-[#FFD700] text-[#0B0B0D] font-bold text-xs"
              >
                <Plus className="w-4 h-4" />
                <span>Add Faculty Profile</span>
              </button>
            }
          />
        ) : (
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-[#17171B] text-[#A1A1AA] border-b border-[#2A2A30]">
                    <th className="py-3.5 px-4 font-semibold">Emp ID</th>
                    <th className="py-3.5 px-4 font-semibold">Full Name</th>
                    <th className="py-3.5 px-4 font-semibold">Email</th>
                    <th className="py-3.5 px-4 font-semibold">Department</th>
                    <th className="py-3.5 px-4 font-semibold">Assigned Divisions</th>
                    <th className="py-3.5 px-4 font-semibold">Status</th>
                    <th className="py-3.5 px-4 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2A2A30]/50 text-[#F5F5F5]">
                  {filtered.map((t) => (
                    <tr key={t.id} className="hover:bg-[#17171B]/50 transition-colors">
                      <td className="py-3.5 px-4 font-bold text-[#FFD700]">{t.employee_id || t.teacher_id}</td>
                      <td className="py-3.5 px-4 font-medium">{t.full_name || t.name}</td>
                      <td className="py-3.5 px-4 text-[#A1A1AA]">{t.email}</td>
                      <td className="py-3.5 px-4">{t.department}</td>
                      <td className="py-3.5 px-4">
                        {(t.assigned_divisions || []).length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {t.assigned_divisions?.map((div: string, i: number) => (
                              <span
                                key={i}
                                className="px-2 py-0.5 rounded-md bg-[#17171B] border border-[#2A2A30] text-[10px] text-[#A1A1AA]"
                              >
                                {div}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-zinc-600 italic">None</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <StatusBadge
                          status={t.is_active ? "verified" : "offline"}
                          labelOverride={t.is_active ? "Active" : "Inactive"}
                        />
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleOpenModal(t)}
                            className="p-1.5 rounded-lg bg-[#17171B] border border-[#2A2A30] text-[#A1A1AA] hover:text-[#FFD700] transition-colors"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => setDeactivatingId(t.id)}
                            className="p-1.5 rounded-lg bg-[#17171B] border border-[#2A2A30] text-[#A1A1AA] hover:text-red-400 transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-4 border-t border-[#2A2A30] flex items-center justify-between text-[11px] text-[#A1A1AA]">
              <span>Showing {filtered.length} faculty records</span>
              <span>FastAPI /teachers data source</span>
            </div>
          </div>
        )}

        {/* Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setIsModalOpen(false)} />
            <div className="relative w-full max-w-lg bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 sm:p-8 shadow-2xl z-10">
              <div className="flex items-center justify-between pb-5 border-b border-[#2A2A30] mb-6">
                <h3 className="text-lg font-bold text-[#F5F5F5]">
                  {editingTeacher ? "Edit Faculty Profile" : "Register New Faculty"}
                </h3>
                <button type="button" onClick={() => setIsModalOpen(false)} className="p-1.5 text-[#A1A1AA]">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSaveTeacher} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Employee ID *</label>
                    <input
                      type="text"
                      required
                      value={formEmpId}
                      onChange={(e) => setFormEmpId(e.target.value)}
                      placeholder="e.g. EMP-104"
                      className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Department *</label>
                    <select
                      value={formDept}
                      onChange={(e) => setFormDept(e.target.value)}
                      className="w-full h-10 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                    >
                      <option value="Computer Science & Engineering">Computer Science & Eng</option>
                      <option value="Artificial Intelligence & Machine Learning">AI & Machine Learning</option>
                      <option value="Information Technology">Information Technology</option>
                      <option value="Electronics & Telecommunication">Electronics & Telecom</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Full Name *</label>
                  <input
                    type="text"
                    required
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder="e.g. Dr. Ananya Sharma"
                    className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">Institutional Email *</label>
                  <input
                    type="email"
                    required
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                    placeholder="faculty@institution.edu"
                    className="w-full h-10 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-semibold text-[#F5F5F5] flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-[#FFD700]" />
                      <span>Assigned Divisions</span>
                    </label>
                    <span className="text-[11px] font-medium text-[#FFD700]/90 bg-[#FFD700]/10 border border-[#FFD700]/20 px-2 py-0.5 rounded-full">
                      {divisionsList.length} division{divisionsList.length === 1 ? "" : "s"} present in system
                    </span>
                  </div>

                  {/* Dropdown Menu Container */}
                  <div className="relative">
                    <div
                      onClick={() => setIsDivDropdownOpen(!isDivDropdownOpen)}
                      className="w-full min-h-[42px] px-3.5 py-2 rounded-xl bg-[#17171B] border border-[#2A2A30] hover:border-[#3A3A42] cursor-pointer flex items-center justify-between transition-colors"
                    >
                      <div className="flex items-center gap-2 flex-wrap">
                        {selectedDivisions.length === 0 ? (
                          <span className="text-xs text-[#A1A1AA]/60">
                            Select divisions to assign ({divisionsList.length} available in system)...
                          </span>
                        ) : (
                          <span className="text-xs font-semibold text-[#F5F5F5]">
                            {selectedDivisions.length} of {divisionsList.length} division{divisionsList.length === 1 ? "" : "s"} assigned
                          </span>
                        )}
                      </div>
                      <ChevronDown
                        className={`w-4 h-4 text-[#A1A1AA] transition-transform duration-200 shrink-0 ${
                          isDivDropdownOpen ? "rotate-180 text-[#FFD700]" : ""
                        }`}
                      />
                    </div>

                    {/* Dropdown Menu List */}
                    {isDivDropdownOpen && (
                      <div className="absolute left-0 right-0 top-full mt-1.5 z-50 bg-[#141418] border border-[#2A2A30] rounded-2xl shadow-2xl p-2.5 space-y-1.5 max-h-64 overflow-y-auto">
                        <div className="flex items-center justify-between px-2 py-1 border-b border-[#2A2A30]/60 pb-1.5">
                          <span className="text-[11px] font-semibold text-[#A1A1AA]">
                            Select from {divisionsList.length} cohorts:
                          </span>
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                selectAllDivisions();
                              }}
                              className="text-[11px] font-bold text-[#FFD700] hover:underline"
                            >
                              Select All ({divisionsList.length})
                            </button>
                            <span className="text-[#2A2A30]">&bull;</span>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                clearAllDivisions();
                              }}
                              className="text-[11px] text-[#A1A1AA] hover:text-[#F5F5F5]"
                            >
                              Clear
                            </button>
                          </div>
                        </div>

                        {divisionsList.length === 0 ? (
                          <div className="p-3 text-center text-xs text-[#A1A1AA]">
                            No academic divisions currently configured.
                          </div>
                        ) : (
                          <div className="space-y-1 pt-1">
                            {divisionsList.map((div) => {
                              const isChecked = selectedDivisions.includes(div.name);
                              return (
                                <div
                                  key={div.id || div.name}
                                  onClick={() => toggleDivision(div.name)}
                                  className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs cursor-pointer transition-colors ${
                                    isChecked
                                      ? "bg-[#FFD700]/10 border border-[#FFD700]/30 text-[#F5F5F5]"
                                      : "hover:bg-[#1A1A20] text-[#A1A1AA] hover:text-[#F5F5F5]"
                                  }`}
                                >
                                  <div className="flex items-center gap-2.5">
                                    <div
                                      className={`w-4 h-4 rounded-md border flex items-center justify-center transition-colors ${
                                        isChecked
                                          ? "bg-[#FFD700] border-[#FFD700] text-[#0B0B0D]"
                                          : "border-[#3A3A42] bg-[#17171B]"
                                      }`}
                                    >
                                      {isChecked && <Check className="w-3 h-3 stroke-[3]" />}
                                    </div>
                                    <span className="font-semibold text-[#F5F5F5]">
                                      Division {div.name}
                                    </span>
                                  </div>
                                  <span className="text-[10px] text-[#A1A1AA]/80 px-2 py-0.5 rounded bg-[#17171B] border border-[#2A2A30]">
                                    {div.department || "Computer Science"}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Selected Division Badges */}
                  {selectedDivisions.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2.5">
                      {selectedDivisions.map((div) => (
                        <span
                          key={div}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#FFD700]/10 border border-[#FFD700]/30 text-xs font-semibold text-[#FFD700]"
                        >
                          <span>Division {div}</span>
                          <button
                            type="button"
                            onClick={() => toggleDivision(div)}
                            className="hover:text-white p-0.5 rounded-full hover:bg-[#FFD700]/20 transition-colors"
                            title={`Remove Division ${div}`}
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Manual Comma-Separated Input Sync */}
                  <div className="mt-2.5">
                    <label className="text-[11px] text-[#A1A1AA] block mb-1">
                      Or edit comma-separated division codes (synced with dropdown):
                    </label>
                    <input
                      type="text"
                      value={formDivisions}
                      onChange={(e) => handleManualDivisionsChange(e.target.value)}
                      placeholder="e.g. A, B, C, AIML A, TE AIML B"
                      className="w-full h-9 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/40 focus:border-[#FFD700] focus:outline-none"
                    />
                  </div>
                </div>

                <div className="pt-4 flex items-center justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-xs font-semibold text-[#A1A1AA]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-6 py-2.5 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs"
                  >
                    {submitting ? "Saving..." : editingTeacher ? "Save Changes" : "Register Faculty"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Deactivate confirmation */}
        {deactivatingId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setDeactivatingId(null)} />
            <div className="relative w-full max-w-sm bg-[#111114] border border-[#2A2A30] rounded-3xl p-6 text-center">
              <div className="w-12 h-12 rounded-full bg-red-950/40 text-red-400 flex items-center justify-center mx-auto mb-4">
                <Trash2 className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-[#F5F5F5]">Deactivate Faculty?</h3>
              <p className="text-xs text-[#A1A1AA] mt-2 mb-6">
                This will prevent lecture creation and attendance review for this instructor.
              </p>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setDeactivatingId(null)}
                  className="flex-1 py-2.5 rounded-xl bg-[#17171B] text-xs text-[#A1A1AA]"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleDeactivate(deactivatingId)}
                  className="flex-1 py-2.5 rounded-xl bg-red-600 text-white font-bold text-xs"
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
