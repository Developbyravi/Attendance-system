"use client";

import React, { useState, type FormEvent } from "react";
import Link from "next/link";
import Logo from "@/components/Logo";
import { supabase } from "@/lib/supabase/client";
import { api } from "@/lib/api";
import { Mail, ArrowLeft, Loader2, CheckCircle2, AlertCircle } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (submitting) return;

    setError(null);
    setSubmitting(true);

    try {
      const { error: supaErr } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: typeof window !== "undefined" ? `${window.location.origin}/auth/callback?type=recovery` : undefined,
      });
      if (supaErr) {
        setError(supaErr.message);
      } else {
        setSubmitted(true);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to initiate password recovery.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0B0B0D] text-[#F5F5F5] flex flex-col justify-between p-6 sm:p-10 font-sans">
      <div className="max-w-[1240px] w-full mx-auto flex items-center justify-between">
        <Logo size="md" href="/" />
        <Link
          href="/login"
          className="text-xs text-[#A1A1AA] hover:text-[#F5F5F5] flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Sign In</span>
        </Link>
      </div>

      <div className="w-full max-w-[440px] mx-auto my-auto py-8">
        <div className="bg-[#111114] border border-[#2A2A30] rounded-3xl p-7 sm:p-9 shadow-[0_30px_80px_-20px_rgba(0,0,0,0.9)]">
          <div className="text-center mb-7">
            <span className="text-[11px] font-bold text-[#FFD700] tracking-[0.18em] uppercase block mb-2">
              ACCOUNT RECOVERY
            </span>
            <h1 className="text-2xl font-extrabold text-[#F5F5F5] font-display">
              Reset Your Password
            </h1>
            <p className="text-xs sm:text-sm text-[#A1A1AA] mt-2">
              Enter your registered institutional email to receive verified password reset instructions.
            </p>
          </div>

          {submitted ? (
            <div className="text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-emerald-950/60 border border-emerald-500/40 text-[#7BD88F] flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-[#F5F5F5]">Recovery Dispatched</h3>
              <p className="text-xs text-[#A1A1AA] leading-relaxed">
                If an authorized account is linked to <strong className="text-[#F5F5F5]">{email}</strong>, password reset steps have been transmitted.
              </p>
              <div className="pt-3">
                <Link
                  href="/login"
                  className="inline-flex items-center justify-center w-full h-11 rounded-xl bg-[#17171B] hover:bg-[#1F1F24] border border-[#2A2A30] text-sm font-semibold text-[#FFD700] transition-colors"
                >
                  Return to Sign In
                </Link>
              </div>
            </div>
          ) : (
            <>
              {error && (
                <div
                  role="alert"
                  className="mb-5 p-3.5 rounded-xl bg-amber-950/30 border border-amber-800/60 text-amber-200 text-xs flex items-start gap-2.5"
                >
                  <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 leading-snug">{error}</div>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="email" className="text-xs font-semibold text-[#F5F5F5] block mb-1.5">
                    Institutional Email Address
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#A1A1AA]">
                      <Mail className="w-4 h-4" />
                    </div>
                    <input
                      id="email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="student@institution.edu"
                      disabled={submitting}
                      className="w-full h-11 pl-10 pr-4 rounded-xl bg-[#17171B] border border-[#2A2A30] text-sm text-[#F5F5F5] placeholder-[#A1A1AA]/50 focus:border-[#FFD700] focus:ring-1 focus:ring-[#FFD700] focus:outline-none transition-colors"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={submitting || !email.trim()}
                  className="w-full h-12 rounded-xl bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-sm tracking-wide flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(255,215,0,0.25)] transition-all disabled:opacity-40"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-[#0B0B0D]" />
                      <span>Sending Instructions...</span>
                    </>
                  ) : (
                    <span>Send Recovery Link</span>
                  )}
                </button>
              </form>

              <div className="mt-6 text-center">
                <Link href="/login" className="text-xs text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors">
                  Remember your password? <span className="text-[#FFD700]">Sign In</span>
                </Link>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="max-w-[1240px] w-full mx-auto text-center text-xs text-[#A1A1AA]/60">
        AIoT SmartAttend &bull; Institutional Authentication Security
      </div>
    </div>
  );
}
