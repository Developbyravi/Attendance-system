"use client";

import React, { useState, type FormEvent } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { ApiError } from "@/lib/api";
import Logo from "@/components/Logo";
import type { UserRole } from "@/types/auth";
import {
  Eye,
  EyeOff,
  Lock,
  User,
  AlertCircle,
  Loader2,
  ArrowRight,
  Shield,
  GraduationCap,
  Users,
  Mail,
  Phone,
  CheckCircle2
} from "lucide-react";

type SignUpRole = "teacher" | "student" | "parent";

const SIGNUP_ROLES: Array<{
  id: SignUpRole;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}> = [
  {
    id: "teacher",
    label: "Faculty",
    icon: Shield,
    description: "Manage lectures, upload classroom verification photos & review attendance",
  },
  {
    id: "student",
    label: "Student",
    icon: GraduationCap,
    description: "Access personal attendance analytics, check-in history & timetable records",
  },
  {
    id: "parent",
    label: "Parent",
    icon: Users,
    description: "Real-time oversight of ward daily arrival check-ins and attendance alerts",
  },
];

export default function SignUpPage() {
  const { register, isLoading: sessionLoading } = useAuth();

  const [role, setRole] = useState<SignUpRole>("teacher");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // Teacher specific
  const [teacherId, setTeacherId] = useState("");
  const [department, setDepartment] = useState("Computer Science & Engineering");

  // Student specific
  const [rollNo, setRollNo] = useState("");
  const [year, setYear] = useState("3rd Year");
  const [division, setDivision] = useState("A");

  // Parent specific
  const [phone, setPhone] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (isSubmitting) return;

    if (password !== confirmPassword) {
      setError("Passwords do not match. Please ensure both passwords match.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      await register({
        role,
        name: fullName.trim(),
        email: email.trim(),
        password,
        teacher_id: role === "teacher" ? teacherId.trim() : undefined,
        department,
        roll_no: role === "student" ? rollNo.trim().toUpperCase() : undefined,
        year: role === "student" ? year : undefined,
        division: role === "student" ? division : undefined,
        phone: role === "parent" ? phone.trim() : undefined,
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Unable to create account with SmartAttend server. Please check connection.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  if (sessionLoading) {
    return (
      <div className="min-h-screen bg-[#0B0B0D] flex flex-col items-center justify-center gap-4 text-[#A1A1AA]">
        <Logo size="lg" />
        <div className="flex items-center gap-2 text-sm">
          <Loader2 className="w-4 h-4 animate-spin text-[#FFD700]" />
          <span>Loading registration portal...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0B0D] text-[#F5F5F5] flex flex-col justify-between p-6 sm:p-10 font-sans selection:bg-[#FFD700]/30 selection:text-[#FFD700]">
      {/* Top Header */}
      <div className="max-w-[1240px] w-full mx-auto flex items-center justify-between">
        <Logo size="md" href="/" />
        <Link
          href="/login"
          className="text-xs text-[#A1A1AA] hover:text-[#FFD700] transition-colors flex items-center gap-1 font-medium"
        >
          <span>Already have an account?</span>
          <span className="text-[#FFD700] font-bold">Sign In &rarr;</span>
        </Link>
      </div>

      {/* Main Form Container */}
      <div className="w-full max-w-xl mx-auto my-8">
        <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-7 sm:p-9 shadow-2xl relative overflow-hidden">
          {/* Subtle Accent Glow */}
          <div className="absolute -top-24 -right-24 w-52 h-52 bg-[#FFD700]/10 rounded-full blur-3xl pointer-events-none" />

          {/* Heading */}
          <div className="mb-7">
            <span className="text-[11px] font-bold text-[#FFD700] tracking-widest uppercase block mb-1">
              CAMPUS ACCESS REGISTRATION
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F5F5F5] tracking-tight">
              Create SmartAttend Account
            </h1>
            <p className="text-xs sm:text-sm text-[#A1A1AA] mt-1.5 leading-relaxed">
              Register your institutional credentials to connect with the AIoT campus attendance system.
            </p>
          </div>

          {/* Role Selection Tabs */}
          <div className="mb-6">
            <label className="block text-xs font-semibold text-[#A1A1AA] mb-2">
              Select Your Institutional Role
            </label>
            <div className="grid grid-cols-3 gap-2">
              {SIGNUP_ROLES.map((r) => {
                const Icon = r.icon;
                const isSelected = role === r.id;
                return (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => {
                      setRole(r.id);
                      setError(null);
                    }}
                    className={`flex flex-col items-center justify-center p-3 rounded-2xl border text-center transition-all ${
                      isSelected
                        ? "bg-[#FFD700]/10 border-[#FFD700] text-[#FFD700] shadow-[0_0_15px_rgba(255,215,0,0.15)]"
                        : "bg-[#17171B] border-[#2A2A30] text-[#A1A1AA] hover:border-[#3A3A42] hover:text-[#F5F5F5]"
                    }`}
                  >
                    <Icon className={`w-5 h-5 mb-1.5 ${isSelected ? "text-[#FFD700]" : "text-[#A1A1AA]"}`} />
                    <span className="text-xs font-bold block">{r.label}</span>
                  </button>
                );
              })}
            </div>
            <p className="text-[11px] text-[#A1A1AA]/80 mt-2 italic">
              {SIGNUP_ROLES.find((r) => r.id === role)?.description}
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-6 p-4 rounded-2xl bg-red-950/50 border border-red-500/50 text-red-300 text-xs flex items-start gap-3">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <div className="leading-relaxed">{error}</div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full Name */}
            <div>
              <label className="block text-xs font-medium text-[#A1A1AA] mb-1.5">
                Full Name <span className="text-[#FFD700]">*</span>
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-[#A1A1AA] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder={
                    role === "teacher"
                      ? "e.g., Dr. Alan Turing"
                      : role === "student"
                      ? "e.g., John Von Neumann"
                      : "e.g., Sarah Neumann"
                  }
                  className="w-full h-11 pl-10 pr-4 rounded-xl bg-[#17171B] border border-[#2A2A30] focus:border-[#FFD700] focus:outline-none text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/50 transition-colors"
                />
              </div>
            </div>

            {/* Email Address */}
            <div>
              <label className="block text-xs font-medium text-[#A1A1AA] mb-1.5">
                Institutional Email <span className="text-[#FFD700]">*</span>
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#A1A1AA] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g., user@smartattend.edu"
                  className="w-full h-11 pl-10 pr-4 rounded-xl bg-[#17171B] border border-[#2A2A30] focus:border-[#FFD700] focus:outline-none text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/50 transition-colors"
                />
              </div>
            </div>

            {/* Role Specific Fields */}
            {role === "teacher" && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-[#A1A1AA] mb-1.5">
                    Faculty / Teacher ID <span className="text-[#FFD700]">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={teacherId}
                    onChange={(e) => setTeacherId(e.target.value)}
                    placeholder="e.g., TCH-2026"
                    className="w-full h-11 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] focus:border-[#FFD700] focus:outline-none text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/50 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-[#A1A1AA] mb-1.5">
                    Department
                  </label>
                  <select
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full h-11 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] focus:border-[#FFD700] focus:outline-none text-xs text-[#F5F5F5] transition-colors"
                  >
                    <option value="Computer Science & Engineering">Computer Science & Engineering</option>
                    <option value="Information Technology">Information Technology</option>
                    <option value="Electronics & Communication">Electronics & Communication</option>
                    <option value="Data Science & AI">Data Science & AI</option>
                  </select>
                </div>
              </div>
            )}

            {role === "student" && (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-[#A1A1AA] mb-1.5">
                      Roll Number / PRN <span className="text-[#FFD700]">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={rollNo}
                      onChange={(e) => setRollNo(e.target.value)}
                      placeholder="e.g., CS2026-042"
                      className="w-full h-11 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] focus:border-[#FFD700] focus:outline-none text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/50 transition-colors uppercase"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-[#A1A1AA] mb-1.5">
                      Division Cohort
                    </label>
                    <select
                      value={division}
                      onChange={(e) => setDivision(e.target.value)}
                      className="w-full h-11 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] focus:border-[#FFD700] focus:outline-none text-xs text-[#F5F5F5] transition-colors"
                    >
                      <option value="A">Division A</option>
                      <option value="B">Division B</option>
                      <option value="C">Division C</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-[#A1A1AA] mb-1.5">
                      Academic Year
                    </label>
                    <select
                      value={year}
                      onChange={(e) => setYear(e.target.value)}
                      className="w-full h-11 px-3 rounded-xl bg-[#17171B] border border-[#2A2A30] focus:border-[#FFD700] focus:outline-none text-xs text-[#F5F5F5] transition-colors"
                    >
                      <option value="1st Year">1st Year</option>
                      <option value="2nd Year">2nd Year</option>
                      <option value="3rd Year">3rd Year</option>
                      <option value="4th Year">4th Year</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-[#A1A1AA] mb-1.5">
                      Department
                    </label>
                    <input
                      type="text"
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      className="w-full h-11 px-3.5 rounded-xl bg-[#17171B] border border-[#2A2A30] focus:border-[#FFD700] focus:outline-none text-xs text-[#F5F5F5] transition-colors"
                    />
                  </div>
                </div>
              </>
            )}

            {role === "parent" && (
              <div>
                <label className="block text-xs font-medium text-[#A1A1AA] mb-1.5">
                  Contact Phone Number <span className="text-[#FFD700]">*</span>
                </label>
                <div className="relative">
                  <Phone className="w-4 h-4 text-[#A1A1AA] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="tel"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="e.g., +1 (555) 019-2834"
                    className="w-full h-11 pl-10 pr-4 rounded-xl bg-[#17171B] border border-[#2A2A30] focus:border-[#FFD700] focus:outline-none text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/50 transition-colors"
                  />
                </div>
              </div>
            )}

            {/* Password & Confirmation */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div>
                <label className="block text-xs font-medium text-[#A1A1AA] mb-1.5">
                  Password <span className="text-[#FFD700]">*</span>
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-[#A1A1AA] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min 6 characters"
                    className="w-full h-11 pl-10 pr-10 rounded-xl bg-[#17171B] border border-[#2A2A30] focus:border-[#FFD700] focus:outline-none text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/50 transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#A1A1AA] hover:text-[#F5F5F5]"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-[#A1A1AA] mb-1.5">
                  Confirm Password <span className="text-[#FFD700]">*</span>
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-[#A1A1AA] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Repeat password"
                    className="w-full h-11 pl-10 pr-4 rounded-xl bg-[#17171B] border border-[#2A2A30] focus:border-[#FFD700] focus:outline-none text-xs text-[#F5F5F5] placeholder-[#A1A1AA]/50 transition-colors"
                  />
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-4">
              <button
                type="submit"
                disabled={isSubmitting || !fullName || !email || !password || !confirmPassword}
                className="w-full h-12 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-sm tracking-wide flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(255,215,0,0.25)] transition-all transform active:scale-[0.99] disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-[#0B0B0D]" />
                    <span>Creating account...</span>
                  </>
                ) : (
                  <>
                    <span>Complete Registration</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Bottom Security Notice */}
          <div className="mt-7 pt-5 border-t border-[#2A2A30]/60 text-center text-xs text-[#A1A1AA]">
            <p className="flex items-center justify-center gap-1.5 text-[11px]">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#7BD88F]" />
              <span>Instant provisioning via FastAPI & Supabase Role-Based Access Control</span>
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="max-w-[1240px] w-full mx-auto text-center text-xs text-[#A1A1AA]/60">
        AIoT SmartAttend Attendance System &bull; Secure Institutional Registration
      </div>
    </div>
  );
}
