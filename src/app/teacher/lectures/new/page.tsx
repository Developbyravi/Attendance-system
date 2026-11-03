"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import DashboardLayout from "@/components/DashboardLayout";
import ProtectedPage from "@/components/ProtectedPage";
import { classService, lectureService, ClassDivisionRecord } from "@/lib/services";
import { ApiError } from "@/lib/api";
import {
  Layers,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  Loader2
} from "lucide-react";

export default function CreateLecturePage() {
  const router = useRouter();

  // Step state (1 to 4)
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  // Divisions available
  const [divisions, setDivisions] = useState<ClassDivisionRecord[]>([]);
  const [loadingDivisions, setLoadingDivisions] = useState(true);

  // Form values
  const [divisionId, setDivisionId] = useState<string>("");
  const [subject, setSubject] = useState("");
  const [lectureTitle, setLectureTitle] = useState("");
  const [lectureDate, setLectureDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [startTime, setStartTime] = useState("10:00 AM");
  const [classroom, setClassroom] = useState("Turing Hall 302");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    classService
      .getAll()
      .then((data) => {
        setDivisions(data);
        if (data.length > 0) setDivisionId(String(data[0].id));
      })
      .catch(() => {})
      .finally(() => setLoadingDivisions(false));
  }, []);

  const selectedDivisionObj = divisions.find((d) => String(d.id) === divisionId);

  async function handleCreateLecture() {
    setError(null);
    setSubmitting(true);

    try {
      const created = await lectureService.create({
        division_id: divisionId,
        division: selectedDivisionObj?.name || divisionId,
        subject: subject.trim(),
        title: lectureTitle.trim(),
        lecture_date: lectureDate,
        start_time: startTime,
        classroom: classroom.trim(),
      });

      // Redirect directly to the lecture details / verification screen
      router.push(`/teacher/lectures/${created.id}`);
    } catch (err: unknown) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Failed to submit lecture creation to FastAPI. Please verify backend connection."
      );
      setSubmitting(false);
    }
  }

  return (
    <ProtectedPage requiredRole="teacher">
      <DashboardLayout
        role="teacher"
        title="Schedule Lecture Session"
        subtitle="Guided workflow to establish a verified classroom attendance register."
        breadcrumbs={[
          { label: "Lectures", href: "/teacher/lectures" },
          { label: "New Session" },
        ]}
      >
        <div className="max-w-2xl mx-auto">
          {/* Progress Indicator */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-3 text-xs">
              <span className={`font-bold ${step >= 1 ? "text-[#FFD700]" : "text-[#A1A1AA]"}`}>
                1. Division
              </span>
              <span className={`font-bold ${step >= 2 ? "text-[#FFD700]" : "text-[#A1A1AA]"}`}>
                2. Subject & Topic
              </span>
              <span className={`font-bold ${step >= 3 ? "text-[#FFD700]" : "text-[#A1A1AA]"}`}>
                3. Time & Room
              </span>
              <span className={`font-bold ${step >= 4 ? "text-[#FFD700]" : "text-[#A1A1AA]"}`}>
                4. Confirmation
              </span>
            </div>
            <div className="w-full bg-[#17171B] h-2 rounded-full overflow-hidden border border-[#2A2A30]">
              <div
                className="bg-gradient-to-r from-[#C9A227] to-[#FFD700] h-full transition-all duration-300"
                style={{ width: `${(step / 4) * 100}%` }}
              />
            </div>
          </div>

          {/* Form Card */}
          <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-7 sm:p-9 shadow-2xl">
            {error && (
              <div className="mb-6 p-4 rounded-2xl bg-red-950/40 border border-red-800/60 text-red-200 text-xs flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <div>{error}</div>
              </div>
            )}

            {/* STEP 1: Select Class & Division */}
            {step === 1 && (
              <div className="space-y-6">
                <div>
                  <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                    STEP 1 OF 4
                  </span>
                  <h3 className="text-xl font-bold text-[#F5F5F5]">Select Division Cohort</h3>
                  <p className="text-xs text-[#A1A1AA] mt-1">
                    Choose the academic batch to link enrolled student rosters.
                  </p>
                </div>

                {loadingDivisions ? (
                  <div className="py-8 text-center text-xs text-[#A1A1AA]">
                    <Loader2 className="w-5 h-5 animate-spin text-[#FFD700] mx-auto mb-2" />
                    <span>Loading authorized academic divisions...</span>
                  </div>
                ) : divisions.length === 0 ? (
                  <div className="p-5 rounded-2xl bg-[#17171B] border border-[#2A2A30] text-center text-xs text-[#A1A1AA]">
                    <Layers className="w-8 h-8 text-[#FFD700] mx-auto mb-2" />
                    <p className="font-bold text-[#F5F5F5]">No Academic Divisions Found</p>
                    <p className="mt-1">
                      An administrator must configure institutional divisions in the Admin portal before creating lectures.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {divisions.map((d) => (
                      <label
                        key={d.id}
                        className={`flex items-center justify-between p-4 rounded-2xl border cursor-pointer transition-all ${
                          divisionId === String(d.id)
                            ? "bg-[#17171B] border-[#FFD700] shadow-[0_0_15px_rgba(255,215,0,0.1)]"
                            : "bg-[#17171B]/50 border-[#2A2A30] hover:border-[#2A2A30]"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <input
                            type="radio"
                            name="division"
                            value={d.id}
                            checked={divisionId === String(d.id)}
                            onChange={() => setDivisionId(String(d.id))}
                            className="text-[#FFD700] focus:ring-[#FFD700]"
                          />
                          <div>
                            <div className="text-sm font-bold text-[#F5F5F5]">{d.name}</div>
                            <div className="text-xs text-[#A1A1AA]">
                              {d.department} &bull; Sem {d.semester}
                            </div>
                          </div>
                        </div>
                        <span className="text-xs font-mono text-[#FFD700]">{d.code}</span>
                      </label>
                    ))}
                  </div>
                )}

                <div className="pt-4 flex justify-end">
                  <button
                    type="button"
                    disabled={!divisionId}
                    onClick={() => setStep(2)}
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs tracking-wider shadow-md transition-all disabled:opacity-50"
                  >
                    <span>Next: Subject & Topic</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 2: Subject & Lecture Title */}
            {step === 2 && (
              <div className="space-y-6">
                <div>
                  <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                    STEP 2 OF 4
                  </span>
                  <h3 className="text-xl font-bold text-[#F5F5F5]">Subject & Lecture Details</h3>
                  <p className="text-xs text-[#A1A1AA] mt-1">
                    Specify curriculum course title and session topic.
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                      Curriculum Subject *
                    </label>
                    <input
                      type="text"
                      required
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      placeholder="e.g. Distributed Computing & IoT"
                      className="w-full h-11 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-sm text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                      Lecture Topic / Title *
                    </label>
                    <input
                      type="text"
                      required
                      value={lectureTitle}
                      onChange={(e) => setLectureTitle(e.target.value)}
                      placeholder="e.g. Unit 4: Microcontroller Architecture"
                      className="w-full h-11 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-sm text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                    />
                  </div>
                </div>

                <div className="pt-4 flex items-center justify-between">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="inline-flex items-center gap-1.5 text-xs text-[#A1A1AA] hover:text-[#F5F5F5]"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Back</span>
                  </button>
                  <button
                    type="button"
                    disabled={!subject.trim() || !lectureTitle.trim()}
                    onClick={() => setStep(3)}
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs tracking-wider shadow-md transition-all disabled:opacity-50"
                  >
                    <span>Next: Date & Classroom</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 3: Date, Time & Classroom */}
            {step === 3 && (
              <div className="space-y-6">
                <div>
                  <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                    STEP 3 OF 4
                  </span>
                  <h3 className="text-xl font-bold text-[#F5F5F5]">Date, Time & Venue</h3>
                  <p className="text-xs text-[#A1A1AA] mt-1">
                    Schedule session time and physical hall.
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                        Lecture Date *
                      </label>
                      <input
                        type="date"
                        required
                        value={lectureDate}
                        onChange={(e) => setLectureDate(e.target.value)}
                        className="w-full h-11 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-sm text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                        Start Time *
                      </label>
                      <input
                        type="text"
                        required
                        value={startTime}
                        onChange={(e) => setStartTime(e.target.value)}
                        placeholder="e.g. 10:00 AM"
                        className="w-full h-11 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-sm text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                      Classroom Hall Venue
                    </label>
                    <input
                      type="text"
                      value={classroom}
                      onChange={(e) => setClassroom(e.target.value)}
                      placeholder="e.g. Block C - Turing Hall 302"
                      className="w-full h-11 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] text-sm text-[#F5F5F5] focus:border-[#FFD700] focus:outline-none"
                    />
                  </div>
                </div>

                <div className="pt-4 flex items-center justify-between">
                  <button
                    type="button"
                    onClick={() => setStep(2)}
                    className="inline-flex items-center gap-1.5 text-xs text-[#A1A1AA] hover:text-[#F5F5F5]"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Back</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setStep(4)}
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs tracking-wider shadow-md transition-all"
                  >
                    <span>Next: Review & Submit</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 4: Review Summary & Submission */}
            {step === 4 && (
              <div className="space-y-6">
                <div>
                  <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                    STEP 4 OF 4
                  </span>
                  <h3 className="text-xl font-bold text-[#F5F5F5]">Review & Establish Register</h3>
                  <p className="text-xs text-[#A1A1AA] mt-1">
                    Confirm lecture parameters. Upon creation, you will upload the classroom photo for AI face cross-check.
                  </p>
                </div>

                <div className="p-5 rounded-2xl bg-[#17171B] border border-[#2A2A30] text-xs space-y-3">
                  <div className="flex justify-between py-1 border-b border-[#2A2A30]/50">
                    <span className="text-[#A1A1AA]">Division Cohort:</span>
                    <span className="font-bold text-[#FFD700]">{selectedDivisionObj?.name || divisionId}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#2A2A30]/50">
                    <span className="text-[#A1A1AA]">Subject:</span>
                    <span className="font-semibold text-[#F5F5F5]">{subject}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#2A2A30]/50">
                    <span className="text-[#A1A1AA]">Topic:</span>
                    <span className="font-semibold text-[#F5F5F5]">{lectureTitle}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#2A2A30]/50">
                    <span className="text-[#A1A1AA]">Date & Time:</span>
                    <span className="text-[#F5F5F5]">{lectureDate} &bull; {startTime}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-[#A1A1AA]">Venue:</span>
                    <span className="text-[#F5F5F5]">{classroom}</span>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-[#17171B]/50 border border-[#2A2A30] text-[11px] text-[#A1A1AA]">
                  <p className="font-bold text-[#F5F5F5] mb-1">Mandatory Business Rule Notice:</p>
                  <p>
                    All active students in this division will be enrolled into this lecture register. Daily RFID taps will be cross-referenced, and classroom photo face embeddings will be checked before teacher review.
                  </p>
                </div>

                <div className="pt-4 flex items-center justify-between">
                  <button
                    type="button"
                    disabled={submitting}
                    onClick={() => setStep(3)}
                    className="inline-flex items-center gap-1.5 text-xs text-[#A1A1AA] hover:text-[#F5F5F5]"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Back</span>
                  </button>
                  <button
                    type="button"
                    disabled={submitting}
                    onClick={handleCreateLecture}
                    className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-xs tracking-wider shadow-[0_0_20px_rgba(255,215,0,0.25)] transition-all disabled:opacity-50"
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-[#0B0B0D]" />
                        <span>Establishing Session...</span>
                      </>
                    ) : (
                      <>
                        <span>Submit & Open Session</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </DashboardLayout>
    </ProtectedPage>
  );
}
