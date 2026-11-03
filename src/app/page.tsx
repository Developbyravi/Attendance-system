"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { ROLE_HOME } from "@/types/auth";
import Logo from "@/components/Logo";
import {
  CreditCard,
  ScanFace,
  TrendingUp,
  Sparkles,
  ArrowRight,
  LayoutDashboard,
  Clock,
  Cpu,
  Menu,
  X
} from "lucide-react";

export default function LandingPage() {
  const { user, isAuthenticated } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Dynamic destination for authenticated users
  const dashboardHref = isAuthenticated && user ? (ROLE_HOME[user.role] ?? "/admin") : "/login";

  return (
    <div className="min-h-screen bg-[#0B0B0D] text-[#F5F5F5] selection:bg-[#FFD700]/30 selection:text-[#FFD700] overflow-x-hidden font-sans">
      {/* ── HEADER / NAVIGATION ── */}
      <header className="sticky top-0 z-50 bg-[#0B0B0D]/85 backdrop-blur-md border-b border-[#2A2A30]/60 transition-all">
        <div className="max-w-[1240px] mx-auto px-6 h-18 flex items-center justify-between">
          {/* Logo */}
          <Logo size="md" href="/" />

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-[14.5px] font-medium text-[#A1A1AA]">
            <a href="#overview" className="hover:text-[#F5F5F5] transition-colors">
              Overview
            </a>
            <a href="#features" className="hover:text-[#F5F5F5] transition-colors">
              Features
            </a>
            <a href="#architecture" className="hover:text-[#F5F5F5] transition-colors">
              Architecture
            </a>
            <a href="#roadmap" className="hover:text-[#F5F5F5] transition-colors">
              Roadmap
            </a>
          </nav>

          {/* Right Action */}
          <div className="hidden md:flex items-center gap-4">
            {isAuthenticated && user ? (
              <Link
                href={dashboardHref}
                className="inline-flex items-center gap-2 bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-[13.5px] tracking-wide px-5 py-2.5 rounded-full shadow-[0_0_20px_rgba(255,215,0,0.25)] transition-all transform active:scale-95"
              >
                <span>DASHBOARD</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  href="/login"
                  className="inline-flex items-center justify-center text-[#A1A1AA] hover:text-[#F5F5F5] font-semibold text-[13.5px] px-3.5 py-2 transition-colors"
                >
                  SIGN IN
                </Link>
                <Link
                  href="/signup"
                  className="inline-flex items-center justify-center bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-[13.5px] tracking-wider px-5 py-2.5 rounded-full shadow-[0_0_20px_rgba(255,215,0,0.25)] transition-all transform active:scale-95"
                >
                  SIGN UP
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-[#A1A1AA] hover:text-[#F5F5F5] hover:bg-[#17171B] transition-colors"
            aria-label="Toggle Navigation"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden border-b border-[#2A2A30] bg-[#111114] px-6 py-5 flex flex-col gap-4 animate-in fade-in slide-in-from-top duration-200">
            <a
              href="#overview"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[#A1A1AA] hover:text-[#F5F5F5] text-base font-medium py-1"
            >
              Overview
            </a>
            <a
              href="#features"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[#A1A1AA] hover:text-[#F5F5F5] text-base font-medium py-1"
            >
              Features
            </a>
            <a
              href="#architecture"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[#A1A1AA] hover:text-[#F5F5F5] text-base font-medium py-1"
            >
              Architecture
            </a>
            <a
              href="#roadmap"
              onClick={() => setMobileMenuOpen(false)}
              className="text-[#A1A1AA] hover:text-[#F5F5F5] text-base font-medium py-1"
            >
              Roadmap
            </a>
            <div className="pt-2 border-t border-[#2A2A30] flex flex-col gap-2">
              <Link
                href={dashboardHref}
                onClick={() => setMobileMenuOpen(false)}
                className="w-full text-center inline-flex items-center justify-center bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-sm tracking-wider px-5 py-3 rounded-full shadow-[0_0_15px_rgba(255,215,0,0.25)] transition-all"
              >
                {isAuthenticated ? "OPEN DASHBOARD" : "SIGN IN"}
              </Link>
              {!isAuthenticated && (
                <Link
                  href="/signup"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center inline-flex items-center justify-center bg-[#17171B] border border-[#2A2A30] hover:border-[#FFD700] text-[#FFD700] font-bold text-sm tracking-wider px-5 py-2.5 rounded-full transition-all"
                >
                  CREATE ACCOUNT
                </Link>
              )}
            </div>
          </div>
        )}
      </header>

      {/* ── HERO SECTION ── */}
      <section
        id="overview"
        className="relative pt-12 md:pt-20 pb-20 md:pb-28 overflow-hidden bg-[radial-gradient(ellipse_800px_500px_at_75%_20%,rgba(255,215,0,0.06),transparent_70%)]"
      >
        <div className="max-w-[1240px] mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* Left Column — Text */}
          <div className="lg:col-span-6 flex flex-col items-start">
            {/* Eyebrow */}
            <span className="text-[#FFD700] text-[11.5px] font-bold tracking-[0.18em] uppercase mb-4 inline-block font-sans">
              AIoT ATTENDANCE MANAGEMENT SYSTEM
            </span>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-[54px] font-extrabold text-[#F5F5F5] tracking-tight leading-[1.08] mb-5 font-display">
              Smarter Attendance. <br className="hidden sm:inline" />
              Verified by AI.
            </h1>

            {/* Supporting Gold Highlight */}
            <p className="text-lg sm:text-[21px] font-semibold text-[#FFD700] leading-snug mb-4 font-sans">
              Smart Attendance. Intelligent Insights. Seamless Integration.
            </p>

            {/* Description */}
            <p className="text-[#A1A1AA] text-base sm:text-[16.5px] leading-relaxed mb-8 max-w-[520px]">
              SmartAttend combines RFID check-ins, AI-assisted face verification, and real-time analytics to make attendance accurate, secure, and effortless for institutions.
            </p>

            {/* CTA Button Row */}
            <div className="flex flex-wrap items-center gap-4 mb-8 w-full sm:w-auto">
              <Link
                href={isAuthenticated ? dashboardHref : "/signup"}
                className="inline-flex items-center justify-center gap-2 bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-[14.5px] px-7 py-3.5 rounded-full shadow-[0_0_25px_rgba(255,215,0,0.3)] transition-all transform hover:-translate-y-0.5 active:translate-y-0"
              >
                <span>{isAuthenticated ? "Explore Dashboard" : "Get Started — Sign Up"}</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href={isAuthenticated ? "#architecture" : "/login"}
                className="inline-flex items-center justify-center gap-2 bg-[#17171B]/80 hover:bg-[#1F1F24] text-[#F5F5F5] hover:text-[#FFD700] border border-[#2A2A30] hover:border-[#C9A227]/50 font-semibold text-[14.5px] px-6 py-3.5 rounded-full transition-all"
              >
                <span>{isAuthenticated ? "View System Architecture" : "Sign In to Portal"}</span>
              </Link>
            </div>

            {/* Subtext Note */}
            <div className="flex items-center gap-2 text-xs sm:text-[13px] text-[#A1A1AA]">
              <span className="text-[#FFD700] font-bold">✦</span>
              <span>Built for intelligent campuses and connected learning environments</span>
            </div>
          </div>

          {/* Right Column — Illustrative Dashboard Card Mockup (Exact to PNG) */}
          <div className="lg:col-span-6 flex justify-center lg:justify-end">
            <div className="w-full max-w-[530px] bg-[#111114] border border-[#2A2A30] rounded-2xl p-6 sm:p-7 shadow-[0_30px_70px_-20px_rgba(0,0,0,0.85)] relative">
              {/* Header inside widget */}
              <div className="flex items-start justify-between mb-5">
                <div>
                  <span className="text-[11px] font-semibold text-[#A1A1AA] tracking-wider uppercase block">
                    SMARTATTEND / OVERVIEW
                  </span>
                  <h3 className="text-lg font-bold text-[#F5F5F5] mt-0.5">
                    Attendance overview
                  </h3>
                </div>
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#17171B] border border-[#2A2A30] text-[11px] font-medium text-[#7BD88F]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#7BD88F] animate-pulse" />
                  <span>Live preview</span>
                </div>
              </div>

              {/* Top 4 Stat Cards in 2x2 grid */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                {/* 1. Today's Attendance */}
                <div className="bg-[#17171B] border border-[#2A2A30]/80 rounded-xl p-3.5">
                  <span className="text-xs text-[#A1A1AA] block mb-1">Today&apos;s Attendance</span>
                  <div className="text-2xl font-bold text-[#F5F5F5] tracking-tight">94.8%</div>
                  <div className="text-[11px] text-[#FFD700] font-medium mt-1 flex items-center gap-1">
                    <span>↗</span> +2.4% this week
                  </div>
                </div>

                {/* 2. Verified Check-Ins */}
                <div className="bg-[#17171B] border border-[#2A2A30]/80 rounded-xl p-3.5">
                  <span className="text-xs text-[#A1A1AA] block mb-1">Verified Check-Ins</span>
                  <div className="text-2xl font-bold text-[#F5F5F5] tracking-tight">1,248</div>
                  <div className="text-[11px] text-[#A1A1AA] mt-1">Across campus</div>
                </div>

                {/* 3. Late Arrivals */}
                <div className="bg-[#17171B] border border-[#2A2A30]/80 rounded-xl p-3.5">
                  <span className="text-xs text-[#A1A1AA] block mb-1">Late Arrivals</span>
                  <div className="text-2xl font-bold text-[#F5F5F5] tracking-tight">37</div>
                  <div className="text-[11px] text-[#A1A1AA] mt-1">Today&apos;s total</div>
                </div>

                {/* 4. System Status */}
                <div className="bg-[#17171B] border border-[#2A2A30]/80 rounded-xl p-3.5">
                  <span className="text-xs text-[#A1A1AA] block mb-1">System Status</span>
                  <div className="text-xs font-semibold text-[#7BD88F] flex items-center gap-1.5 mt-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#7BD88F]" />
                    <span>All systems operational</span>
                  </div>
                  <div className="text-[11px] text-[#A1A1AA] mt-1">Devices connected</div>
                </div>
              </div>

              {/* Bottom Row Split: Bar Chart on Left, Live Activity on Right */}
              <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 mb-3">
                {/* Attendance Trend Bar Chart */}
                <div className="sm:col-span-7 bg-[#17171B] border border-[#2A2A30]/80 rounded-xl p-3.5 flex flex-col justify-between">
                  <span className="text-xs text-[#A1A1AA] block mb-3 font-medium">Attendance trend</span>
                  <div className="flex items-end justify-between gap-1.5 h-20 pt-2 px-1">
                    {[
                      { day: "MON", h: "45%" },
                      { day: "TUE", h: "60%" },
                      { day: "WED", h: "52%" },
                      { day: "THU", h: "75%" },
                      { day: "FRI", h: "68%" },
                      { day: "SAT", h: "85%" },
                      { day: "SUN", h: "80%" },
                    ].map((bar, i) => (
                      <div key={i} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                        <div
                          className="w-full rounded-sm bg-gradient-to-t from-[#C9A227] to-[#FFD700]"
                          style={{ height: bar.h }}
                        />
                        <span className="text-[9px] text-[#A1A1AA] tracking-tighter">{bar.day}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Live Activity */}
                <div className="sm:col-span-5 bg-[#17171B] border border-[#2A2A30]/80 rounded-xl p-3.5 flex flex-col justify-between">
                  <span className="text-xs text-[#A1A1AA] block mb-2 font-medium">Live activity</span>
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#FFD700]" />
                        <span className="text-[#F5F5F5]">RFID check-in</span>
                      </div>
                      <span className="text-[#A1A1AA] text-[11px]">09:42</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#FFD700]" />
                        <span className="text-[#F5F5F5]">Face AI verified</span>
                      </div>
                      <span className="text-[#A1A1AA] text-[11px]">09:38</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#FFD700]" />
                        <span className="text-[#F5F5F5]">Gateway synced</span>
                      </div>
                      <span className="text-[#A1A1AA] text-[11px]">09:31</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom Disclosure note */}
              <div className="text-right">
                <span className="text-[10px] text-[#A1A1AA]/70 italic">
                  Illustrative project preview
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── SECTION 2: CAPABILITIES (4 CARDS) ── */}
      <section id="features" className="py-20 md:py-24 border-t border-[#2A2A30]/60 bg-[#0B0B0D]">
        <div className="max-w-[1240px] mx-auto px-6">
          <div className="mb-12">
            <span className="text-[#FFD700] text-[11.5px] font-bold tracking-[0.18em] uppercase block mb-3">
              CAPABILITIES
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F5F5F5] tracking-tight font-display">
              One intelligent layer for every check-in
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* 1. RFID Daily Check-in */}
            <div className="bg-[#17171B] border border-[#2A2A30] hover:border-[#C9A227]/40 rounded-2xl p-6 transition-all duration-200 group">
              <div className="w-11 h-11 rounded-xl bg-[#111114] border border-[#2A2A30] flex items-center justify-center text-[#FFD700] mb-5 group-hover:border-[#FFD700]/40 transition-colors">
                <CreditCard className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[#F5F5F5] mb-2">RFID Daily Check-in</h3>
              <p className="text-sm text-[#A1A1AA] leading-relaxed">
                Fast tap-based attendance capture with reliable device connectivity.
              </p>
            </div>

            {/* 2. AI Face Verification */}
            <div className="bg-[#17171B] border border-[#2A2A30] hover:border-[#C9A227]/40 rounded-2xl p-6 transition-all duration-200 group">
              <div className="w-11 h-11 rounded-xl bg-[#111114] border border-[#2A2A30] flex items-center justify-center text-[#FFD700] mb-5 group-hover:border-[#FFD700]/40 transition-colors">
                <ScanFace className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[#F5F5F5] mb-2">AI Face Verification</h3>
              <p className="text-sm text-[#A1A1AA] leading-relaxed">
                AI-assisted identity confirmation to reduce proxy attendance and improve trust.
              </p>
            </div>

            {/* 3. Real-time Insights */}
            <div className="bg-[#17171B] border border-[#2A2A30] hover:border-[#C9A227]/40 rounded-2xl p-6 transition-all duration-200 group">
              <div className="w-11 h-11 rounded-xl bg-[#111114] border border-[#2A2A30] flex items-center justify-center text-[#FFD700] mb-5 group-hover:border-[#FFD700]/40 transition-colors">
                <TrendingUp className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[#F5F5F5] mb-2">Real-time Insights</h3>
              <p className="text-sm text-[#A1A1AA] leading-relaxed">
                Clear dashboards for attendance trends, late arrivals, and participation patterns.
              </p>
            </div>

            {/* 4. Seamless Integration */}
            <div className="bg-[#17171B] border border-[#2A2A30] hover:border-[#C9A227]/40 rounded-2xl p-6 transition-all duration-200 group">
              <div className="w-11 h-11 rounded-xl bg-[#111114] border border-[#2A2A30] flex items-center justify-center text-[#FFD700] mb-5 group-hover:border-[#FFD700]/40 transition-colors">
                <Sparkles className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[#F5F5F5] mb-2">Seamless Integration</h3>
              <p className="text-sm text-[#A1A1AA] leading-relaxed">
                Connect devices, student records, and institutional workflows in one platform.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── SECTION 3: SYSTEM ARCHITECTURE (HORIZONTAL FLOW) ── */}
      <section id="architecture" className="py-20 md:py-24 border-t border-[#2A2A30]/60 bg-[#0B0B0D]">
        <div className="max-w-[1240px] mx-auto px-6">
          <div className="mb-14">
            <span className="text-[#FFD700] text-[11.5px] font-bold tracking-[0.18em] uppercase block mb-3">
              SYSTEM ARCHITECTURE
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F5F5F5] tracking-tight mb-3 font-display">
              From tap to insight, in seconds.
            </h2>
            <p className="text-sm sm:text-base text-[#A1A1AA] max-w-2xl leading-relaxed">
              A secure, traceable flow moves each event from connected hardware to near-real-time decisions, so staff can act on dependable attendance information.
            </p>
          </div>

          {/* 5 Connected Architecture Nodes */}
          <div className="relative">
            {/* Connecting horizontal line */}
            <div className="hidden lg:block absolute top-[28px] left-[5%] right-[5%] h-[2px] bg-gradient-to-r from-[#C9A227]/30 via-[#FFD700] to-[#C9A227]/30 z-0" />

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6 relative z-10">
              {[
                {
                  step: "01",
                  title: "RFID Reader",
                  desc: "Student taps card or tag.",
                },
                {
                  step: "02",
                  title: "IoT Gateway",
                  desc: "Securely transmits the event.",
                },
                {
                  step: "03",
                  title: "AI Verification",
                  desc: "Cross-checks identity when enabled.",
                },
                {
                  step: "04",
                  title: "SmartAttend Cloud",
                  desc: "Validates and processes records.",
                },
                {
                  step: "05",
                  title: "Analytics Dashboard",
                  desc: "Staff see live insights.",
                },
              ].map((item, index) => (
                <div
                  key={index}
                  className="bg-[#17171B] border border-[#2A2A30] hover:border-[#FFD700]/50 rounded-2xl p-5 sm:p-6 transition-all duration-200"
                >
                  <div className="flex items-center gap-2 mb-4">
                    <span className="text-xs font-bold text-[#FFD700]">{item.step}</span>
                    <span className="w-1.5 h-1.5 rounded-full bg-[#FFD700]" />
                  </div>
                  <h4 className="text-base font-bold text-[#F5F5F5] mb-2">{item.title}</h4>
                  <p className="text-xs sm:text-[13px] text-[#A1A1AA] leading-relaxed">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── SECTION 4: THE CONTROL CENTER (DASHBOARD PREVIEW MOCKUP) ── */}
      <section className="py-20 md:py-24 border-t border-[#2A2A30]/60 bg-[#0B0B0D]">
        <div className="max-w-[1240px] mx-auto px-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-10">
            <div>
              <span className="text-[#FFD700] text-[11.5px] font-bold tracking-[0.18em] uppercase block mb-3">
                THE CONTROL CENTER
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F5F5F5] tracking-tight font-display">
                Designed for clarity at every level
              </h2>
            </div>
            <div className="inline-flex items-center gap-2 self-start sm:self-auto px-3.5 py-1.5 rounded-full bg-[#17171B] border border-[#C9A227]/40 text-xs font-medium text-[#FFD700] shadow-[0_0_15px_rgba(255,215,0,0.15)]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#FFD700] animate-ping" />
              <span>Live monitoring preview</span>
            </div>
          </div>

          {/* Large Dashboard Mockup Container */}
          <div className="bg-[#111114] border border-[#2A2A30] rounded-2xl sm:rounded-3xl overflow-hidden shadow-[0_30px_90px_-20px_rgba(0,0,0,0.9)]">
            <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[560px]">
              {/* Left Mini-Sidebar */}
              <div className="hidden lg:flex lg:col-span-3 border-r border-[#2A2A30] bg-[#0E0E11] p-6 flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2.5 mb-8">
                    <Logo size="sm" showText={true} />
                  </div>

                  <nav className="space-y-1.5 text-xs font-medium">
                    <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-[#17171B] text-[#FFD700] border border-[#2A2A30]">
                      <LayoutDashboard className="w-4 h-4 text-[#FFD700]" />
                      <span>Overview</span>
                    </div>
                    <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors">
                      <Clock className="w-4 h-4" />
                      <span>Attendance</span>
                    </div>
                    <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors">
                      <Cpu className="w-4 h-4" />
                      <span>Devices</span>
                    </div>
                    <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-[#A1A1AA] hover:text-[#F5F5F5] transition-colors">
                      <TrendingUp className="w-4 h-4" />
                      <span>Reports</span>
                    </div>
                  </nav>
                </div>

                <div className="pt-6 border-t border-[#2A2A30]/60 text-[11px] text-[#A1A1AA]">
                  <p className="font-semibold text-[#F5F5F5]">Campus workspace</p>
                  <p className="text-[10px] text-[#A1A1AA]/70">Project preview</p>
                </div>
              </div>

              {/* Main Content Area */}
              <div className="lg:col-span-9 p-6 sm:p-8 flex flex-col justify-between">
                <div>
                  {/* Top bar inside preview */}
                  <div className="flex items-center justify-between pb-6 border-b border-[#2A2A30]/60 mb-6">
                    <div>
                      <span className="text-[11px] text-[#A1A1AA] tracking-wider uppercase block">
                        MONITORING / OVERVIEW
                      </span>
                      <h3 className="text-xl font-bold text-[#F5F5F5]">Campus attendance</h3>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-[#7BD88F]">
                      <span className="w-2 h-2 rounded-full bg-[#7BD88F]" />
                      <span>Devices online</span>
                    </div>
                  </div>

                  {/* Top 3 Stat Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                    <div className="bg-[#17171B] border border-[#2A2A30] rounded-xl p-4">
                      <span className="text-xs text-[#A1A1AA] block mb-1">Attendance rate</span>
                      <div className="text-2xl font-bold text-[#F5F5F5]">94.8%</div>
                    </div>
                    <div className="bg-[#17171B] border border-[#2A2A30] rounded-xl p-4">
                      <span className="text-xs text-[#A1A1AA] block mb-1">Check-ins today</span>
                      <div className="text-2xl font-bold text-[#F5F5F5]">1,248</div>
                    </div>
                    <div className="bg-[#17171B] border border-[#2A2A30] rounded-xl p-4">
                      <span className="text-xs text-[#A1A1AA] block mb-1">To review</span>
                      <div className="text-2xl font-bold text-[#F5F5F5]">12</div>
                    </div>
                  </div>

                  {/* Middle Row: Trend & Weekly Summary */}
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-4 mb-6">
                    {/* Attendance trend bars */}
                    <div className="md:col-span-7 bg-[#17171B] border border-[#2A2A30] rounded-xl p-4">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-xs font-semibold text-[#F5F5F5]">Attendance trend</span>
                        <span className="text-[11px] text-[#A1A1AA]">This week</span>
                      </div>
                      <div className="flex items-end justify-between gap-3 h-24 pt-3 px-2">
                        {[
                          { d: "MON", h: "60%" },
                          { d: "TUE", h: "82%" },
                          { d: "WED", h: "68%" },
                          { d: "THU", h: "88%" },
                          { d: "FRI", h: "76%" },
                        ].map((b, i) => (
                          <div key={i} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
                            <div
                              className="w-full rounded-sm bg-gradient-to-t from-[#C9A227] to-[#FFD700]"
                              style={{ height: b.h }}
                            />
                            <span className="text-[10px] text-[#A1A1AA]">{b.d}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Weekly summary progress */}
                    <div className="md:col-span-5 bg-[#17171B] border border-[#2A2A30] rounded-xl p-4 flex flex-col justify-between">
                      <div>
                        <span className="text-xs font-semibold text-[#F5F5F5] block mb-4">Weekly summary</span>
                        <div className="space-y-3.5">
                          <div>
                            <div className="flex justify-between text-xs mb-1.5">
                              <span className="text-[#A1A1AA]">On-time check-ins</span>
                              <span className="font-semibold text-[#F5F5F5]">92%</span>
                            </div>
                            <div className="w-full bg-[#2A2A30] h-2 rounded-full overflow-hidden">
                              <div className="bg-gradient-to-r from-[#C9A227] to-[#FFD700] h-full w-[92%]" />
                            </div>
                          </div>
                          <div>
                            <div className="flex justify-between text-xs mb-1.5">
                              <span className="text-[#A1A1AA]">Face AI verified</span>
                              <span className="font-semibold text-[#F5F5F5]">86%</span>
                            </div>
                            <div className="w-full bg-[#2A2A30] h-2 rounded-full overflow-hidden">
                              <div className="bg-gradient-to-r from-[#C9A227] to-[#FFD700] h-full w-[86%]" />
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="text-[11px] text-[#A1A1AA] pt-2 flex items-center gap-1">
                        <span>Compared with last 7 days</span>
                        <span className="text-[#FFD700]">↗</span>
                      </div>
                    </div>
                  </div>

                  {/* Bottom Row: Recent check-ins table & Device health */}
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
                    {/* Table */}
                    <div className="md:col-span-7 bg-[#17171B] border border-[#2A2A30] rounded-xl p-4">
                      <span className="text-xs font-semibold text-[#F5F5F5] block mb-3">Recent check-ins</span>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-[11px]">
                          <thead>
                            <tr className="text-[#A1A1AA] border-b border-[#2A2A30]/60">
                              <th className="pb-2 font-medium">Student</th>
                              <th className="pb-2 font-medium">ID</th>
                              <th className="pb-2 font-medium">Check-in</th>
                              <th className="pb-2 font-medium">Method</th>
                              <th className="pb-2 font-medium">Status</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-[#2A2A30]/40 text-[#F5F5F5]">
                            {[
                              { name: "Alex Morgan", id: "ST-1042", time: "09:42", method: "RFID", status: "Verified", color: "text-[#7BD88F]" },
                              { name: "Priya Shah", id: "ST-1088", time: "09:38", method: "Face AI", status: "Verified", color: "text-[#7BD88F]" },
                              { name: "Jordan Lee", id: "ST-1107", time: "09:31", method: "RFID", status: "Review", color: "text-[#FFD700]" },
                              { name: "Sam Taylor", id: "ST-1124", time: "09:25", method: "Face AI", status: "Verified", color: "text-[#7BD88F]" },
                            ].map((row, i) => (
                              <tr key={i} className="hover:bg-[#111114]/50">
                                <td className="py-2.5 font-medium">{row.name}</td>
                                <td className="py-2.5 text-[#A1A1AA]">{row.id}</td>
                                <td className="py-2.5 text-[#A1A1AA]">{row.time}</td>
                                <td className="py-2.5">{row.method}</td>
                                <td className={`py-2.5 font-medium ${row.color}`}>
                                  ● {row.status}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Device Health */}
                    <div className="md:col-span-5 bg-[#17171B] border border-[#2A2A30] rounded-xl p-4 flex flex-col justify-between">
                      <div>
                        <span className="text-xs font-semibold text-[#F5F5F5] block mb-3">Device health</span>
                        <div className="space-y-2.5 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="text-[#A1A1AA]">Main entrance</span>
                            <span className="text-[#7BD88F] font-medium">Online</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-[#A1A1AA]">Science block</span>
                            <span className="text-[#7BD88F] font-medium">Online</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-[#A1A1AA]">North gateway</span>
                            <span className="text-[#7BD88F] font-medium">Online</span>
                          </div>
                        </div>
                      </div>
                      <div className="mt-4 pt-3 border-t border-[#2A2A30]/60">
                        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#111114] border border-[#2A2A30] text-[11px] text-[#FFD700]">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#7BD88F]" />
                          <span>3 of 3 devices healthy</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-[#2A2A30]/60 text-right">
                  <span className="text-[11px] text-[#A1A1AA]/80 italic">
                    Illustrative interface and sample records for exhibition purposes.
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 4 Feature Pills Below Mockup */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            {[
              "Faster check-ins",
              "Reduced proxy attendance",
              "Real-time visibility",
              "IoT-ready infrastructure",
            ].map((text, i) => (
              <div
                key={i}
                className="bg-[#17171B] border border-[#2A2A30] rounded-xl p-4 text-center text-xs sm:text-[13px] font-semibold text-[#F5F5F5] flex items-center justify-center gap-2"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-[#FFD700]" />
                <span>{text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SECTION 5: FUTURE ROADMAP ── */}
      <section id="roadmap" className="py-20 md:py-24 border-t border-[#2A2A30]/60 bg-[#0B0B0D]">
        <div className="max-w-[1240px] mx-auto px-6">
          <div className="mb-12">
            <span className="text-[#FFD700] text-[11.5px] font-bold tracking-[0.18em] uppercase block mb-3">
              FUTURE ROADMAP
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F5F5F5] tracking-tight font-display">
              Built for what&apos;s next
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Phase 01 */}
            <div className="bg-[#17171B] border border-[#2A2A30] rounded-2xl p-6 relative">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-1.5 text-xs font-bold text-[#FFD700]">
                  <span className="w-2 h-2 rounded-full bg-[#FFD700]" />
                  <span>PHASE 01</span>
                </div>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-[#111114] border border-[#2A2A30] text-[#7BD88F] font-medium">
                  Available
                </span>
              </div>
              <h3 className="text-base font-bold text-[#F5F5F5] mb-2">Connected Check-ins</h3>
              <p className="text-xs sm:text-[13px] text-[#A1A1AA] leading-relaxed">
                RFID and device onboarding.
              </p>
            </div>

            {/* Phase 02 */}
            <div className="bg-[#17171B] border border-[#2A2A30] rounded-2xl p-6 relative">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-1.5 text-xs font-bold text-[#FFD700]">
                  <span className="w-2 h-2 rounded-full bg-[#FFD700]" />
                  <span>PHASE 02</span>
                </div>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-[#111114] border border-[#2A2A30] text-[#7BD88F] font-medium">
                  Available
                </span>
              </div>
              <h3 className="text-base font-bold text-[#F5F5F5] mb-2">AI Verification</h3>
              <p className="text-xs sm:text-[13px] text-[#A1A1AA] leading-relaxed">
                Face-assisted identity validation.
              </p>
            </div>

            {/* Phase 03 */}
            <div className="bg-[#17171B] border border-[#2A2A30] rounded-2xl p-6 relative">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-1.5 text-xs font-bold text-[#A1A1AA]">
                  <span className="w-2 h-2 rounded-full border border-[#A1A1AA]" />
                  <span>PHASE 03</span>
                </div>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-[#111114] border border-[#2A2A30] text-[#A1A1AA] font-medium">
                  Planned
                </span>
              </div>
              <h3 className="text-base font-bold text-[#F5F5F5] mb-2">Predictive Insights</h3>
              <p className="text-xs sm:text-[13px] text-[#A1A1AA] leading-relaxed">
                Early signals for attendance risk.
              </p>
            </div>

            {/* Phase 04 */}
            <div className="bg-[#17171B] border border-[#2A2A30] rounded-2xl p-6 relative">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-1.5 text-xs font-bold text-[#A1A1AA]">
                  <span className="w-2 h-2 rounded-full border border-[#A1A1AA]" />
                  <span>PHASE 04</span>
                </div>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-[#111114] border border-[#2A2A30] text-[#A1A1AA] font-medium">
                  Planned
                </span>
              </div>
              <h3 className="text-base font-bold text-[#F5F5F5] mb-2">Smart Campus Scale</h3>
              <p className="text-xs sm:text-[13px] text-[#A1A1AA] leading-relaxed">
                Broader IoT integrations and institution-wide automation.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── SECTION 6: THE NEXT STEP (FINAL CTA) ── */}
      <section className="py-24 border-t border-[#2A2A30]/60 bg-[radial-gradient(ellipse_600px_350px_at_50%_40%,rgba(255,215,0,0.08),transparent_70%)] text-center">
        <div className="max-w-[760px] mx-auto px-6">
          <span className="text-[#FFD700] text-[11.5px] font-bold tracking-[0.18em] uppercase block mb-3">
            THE NEXT STEP
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-[44px] font-extrabold text-[#F5F5F5] tracking-tight leading-tight mb-4 font-display">
            Make every attendance record more intelligent.
          </h2>
          <p className="text-sm sm:text-base text-[#A1A1AA] leading-relaxed mb-8 max-w-xl mx-auto">
            Bring trusted check-ins, connected devices, and actionable insights into one seamless experience.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 mb-4">
            <Link
              href={dashboardHref}
              className="inline-flex items-center justify-center gap-2 bg-[#FFD700] hover:bg-[#FFE34D] text-[#0B0B0D] font-bold text-[14.5px] px-8 py-3.5 rounded-full shadow-[0_0_25px_rgba(255,215,0,0.3)] transition-all transform hover:-translate-y-0.5"
            >
              <span>Explore Dashboard</span>
            </Link>
            <a
              href="#architecture"
              className="inline-flex items-center justify-center gap-2 bg-[#17171B] hover:bg-[#1F1F24] text-[#F5F5F5] border border-[#2A2A30] font-semibold text-[14.5px] px-6 py-3.5 rounded-full transition-all"
            >
              <span>Explore the Architecture</span>
            </a>
          </div>

          <p className="text-xs text-[#A1A1AA]/70">
            Explore the illustrative dashboard preview above.
          </p>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-[#2A2A30] bg-[#0E0E11] py-12 text-sm text-[#A1A1AA]">
        <div className="max-w-[1240px] mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Left Brand Details */}
          <div className="flex flex-col items-center md:items-start gap-2">
            <Logo size="sm" href="/" />
            <p className="text-xs text-[#A1A1AA]">
              Smart Attendance. Intelligent Insights. Seamless Integration.
            </p>
            <p className="text-[11px] text-[#A1A1AA]/60">
              AIoT SmartAttend · Engineering Project Exhibition
            </p>
          </div>

          {/* Right Navigation Links */}
          <div className="flex items-center gap-6 text-xs font-medium">
            <a href="#overview" className="hover:text-[#F5F5F5] transition-colors">
              Overview
            </a>
            <a href="#features" className="hover:text-[#F5F5F5] transition-colors">
              Features
            </a>
            <a href="#architecture" className="hover:text-[#F5F5F5] transition-colors">
              Architecture
            </a>
            <a href="#roadmap" className="hover:text-[#F5F5F5] transition-colors">
              Roadmap
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
