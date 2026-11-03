"use client";

import React, { useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import Logo from "@/components/Logo";
import type { UserRole } from "@/types/auth";
import { ROLE_DISPLAY } from "@/types/auth";
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  Layers,
  Radio,
  BarChart3,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronRight,
  Calendar,
  BookOpen,
  UserCheck,
  PlusCircle,
  History,
  MessageSquare
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  exact?: boolean;
}

const ADMIN_NAV: NavItem[] = [
  { label: "Dashboard",             href: "/admin",            icon: LayoutDashboard, exact: true },
  { label: "Students",              href: "/admin/students",   icon: GraduationCap },
  { label: "Teachers",              href: "/admin/teachers",   icon: Users },
  { label: "Classes & Divisions",   href: "/admin/classes",    icon: Layers },
  { label: "RFID Devices",          href: "/admin/devices",    icon: Radio },
  { label: "Institution Attendance",href: "/admin/attendance", icon: UserCheck },
  { label: "Reports & Analytics",   href: "/admin/reports",    icon: BarChart3 },
  { label: "System Settings",       href: "/admin/settings",   icon: Settings },
];

const TEACHER_NAV: NavItem[] = [
  { label: "Overview",              href: "/teacher",               icon: LayoutDashboard, exact: true },
  { label: "Daily Check-ins",       href: "/teacher/daily-checkins",icon: UserCheck },
  { label: "Lecture Sessions",      href: "/teacher/lectures",      icon: BookOpen },
  { label: "Create Lecture",        href: "/teacher/lectures/new",  icon: PlusCircle },
  { label: "Attendance History",    href: "/teacher/attendance",    icon: History },
  { label: "Assigned Students",     href: "/teacher/students",      icon: GraduationCap },
  { label: "Reports",               href: "/teacher/reports",       icon: BarChart3 },
];

const STUDENT_NAV: NavItem[] = [
  { label: "My Dashboard",          href: "/student",            icon: LayoutDashboard, exact: true },
  { label: "Attendance History",    href: "/student/attendance", icon: Calendar },
  { label: "Attendance Analytics",  href: "/student/analytics",  icon: BarChart3 },
  { label: "Student Profile",       href: "/student/profile",    icon: GraduationCap },
];

const PARENT_NAV: NavItem[] = [
  { label: "Child Overview",        href: "/parent",               icon: LayoutDashboard, exact: true },
  { label: "Attendance Records",    href: "/parent/attendance",    icon: Calendar },
  { label: "Notifications",         href: "/parent/notifications", icon: MessageSquare },
  { label: "Profile & Preferences", href: "/parent/profile",       icon: Settings },
];

const NAV_MAP: Record<UserRole, NavItem[]> = {
  admin: ADMIN_NAV,
  teacher: TEACHER_NAV,
  student: STUDENT_NAV,
  parent: PARENT_NAV,
};

interface DashboardLayoutProps {
  children: ReactNode;
  role: UserRole;
  title: string;
  subtitle?: string;
  breadcrumbs?: Array<{ label: string; href?: string }>;
  actions?: ReactNode;
}

export default function DashboardLayout({
  children,
  role,
  title,
  subtitle,
  breadcrumbs = [],
  actions,
}: DashboardLayoutProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  const navItems = NAV_MAP[role] || [];
  const roleDisplay = ROLE_DISPLAY[role] || role;

  return (
    <div className="min-h-screen bg-[#0B0B0D] text-[#F5F5F5] flex font-sans selection:bg-[#FFD700]/30 selection:text-[#FFD700]">
      {/* ── DESKTOP SIDEBAR ── */}
      <aside className="hidden lg:flex w-64 bg-[#0E0E11] border-r border-[#2A2A30] flex-col justify-between shrink-0 fixed inset-y-0 z-40">
        <div>
          {/* Logo Brand Header */}
          <div className="h-18 px-6 flex items-center border-b border-[#2A2A30]/80">
            <Logo size="md" href="/" />
          </div>

          {/* Role Identifier Badge */}
          <div className="px-6 py-4">
            <div className="px-3 py-1.5 rounded-xl bg-[#17171B] border border-[#2A2A30] flex items-center justify-between">
              <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase">
                {roleDisplay}
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-[#7BD88F]" />
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="px-3 space-y-1">
            {navItems.map((item) => {
              const IconComponent = item.icon;
              const isActive = item.exact
                ? pathname === item.href
                : pathname === item.href || pathname.startsWith(item.href + "/");

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? "bg-[#17171B] text-[#FFD700] border border-[#2A2A30] shadow-[0_0_15px_rgba(255,215,0,0.08)]"
                      : "text-[#A1A1AA] hover:text-[#F5F5F5] hover:bg-[#141418]"
                  }`}
                >
                  <IconComponent
                    className={`w-4 h-4 transition-colors ${
                      isActive ? "text-[#FFD700]" : "text-[#A1A1AA]"
                    }`}
                  />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer with Hardware Kiosk link & Sign out */}
        <div className="p-4 border-t border-[#2A2A30]/80 space-y-2">
          <Link
            href="/kiosk"
            target="_blank"
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs text-[#A1A1AA] hover:text-[#FFD700] hover:bg-[#141418] transition-colors"
          >
            <Radio className="w-3.5 h-3.5 text-[#FFD700]" />
            <span>Launch RFID Kiosk</span>
          </Link>
          <button
            type="button"
            onClick={logout}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs text-red-400 hover:bg-red-950/30 hover:text-red-300 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* ── MOBILE DRAWER NAVIGATION ── */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-black/80 backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="relative w-72 bg-[#0E0E11] border-r border-[#2A2A30] p-6 flex flex-col justify-between z-10 animate-in slide-in-from-left duration-200">
            <div>
              <div className="flex items-center justify-between pb-6 border-b border-[#2A2A30]">
                <Logo size="sm" href="/" />
                <button
                  type="button"
                  onClick={() => setSidebarOpen(false)}
                  className="p-1.5 rounded-lg text-[#A1A1AA] hover:text-[#F5F5F5]"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="py-4">
                <span className="text-[11px] font-bold text-[#FFD700] tracking-wider uppercase block mb-1">
                  {roleDisplay} Workspace
                </span>
                <span className="text-xs text-[#A1A1AA]">{user?.full_name || user?.username}</span>
              </div>

              <nav className="space-y-1">
                {navItems.map((item) => {
                  const IconComponent = item.icon;
                  const isActive = item.exact
                    ? pathname === item.href
                    : pathname === item.href || pathname.startsWith(item.href + "/");

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold ${
                        isActive
                          ? "bg-[#17171B] text-[#FFD700] border border-[#2A2A30]"
                          : "text-[#A1A1AA] hover:text-[#F5F5F5]"
                      }`}
                    >
                      <IconComponent className="w-4 h-4" />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </nav>
            </div>

            <div className="pt-4 border-t border-[#2A2A30] space-y-2">
              <Link
                href="/kiosk"
                className="flex items-center gap-2 px-3 py-2 text-xs text-[#A1A1AA] hover:text-[#FFD700]"
              >
                <Radio className="w-3.5 h-3.5 text-[#FFD700]" />
                <span>Launch RFID Kiosk</span>
              </Link>
              <button
                type="button"
                onClick={logout}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs text-red-400"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── MAIN CONTENT WRAPPER ── */}
      <div className="flex-1 lg:pl-64 flex flex-col min-w-0">
        {/* Top Navbar */}
        <header className="h-18 sticky top-0 z-30 bg-[#0B0B0D]/85 backdrop-blur-md border-b border-[#2A2A30]/80 px-6 sm:px-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-xl bg-[#17171B] border border-[#2A2A30] text-[#A1A1AA] hover:text-[#F5F5F5]"
              aria-label="Toggle Navigation"
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Breadcrumbs */}
            <div className="hidden sm:flex items-center gap-2 text-xs text-[#A1A1AA]">
              <Link href={NAV_MAP[role][0].href} className="hover:text-[#F5F5F5] transition-colors">
                {roleDisplay}
              </Link>
              {breadcrumbs.map((b, i) => (
                <React.Fragment key={i}>
                  <ChevronRight className="w-3.5 h-3.5 text-[#2A2A30]" />
                  {b.href ? (
                    <Link href={b.href} className="hover:text-[#F5F5F5] transition-colors">
                      {b.label}
                    </Link>
                  ) : (
                    <span className="text-[#F5F5F5] font-medium">{b.label}</span>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* User profile dropdown and status */}
          <div className="flex items-center gap-4">
            <div className="relative">
              <button
                type="button"
                onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                className="flex items-center gap-3 p-1.5 pl-3 rounded-full bg-[#17171B] border border-[#2A2A30] hover:border-[#C9A227]/40 transition-colors"
              >
                <div className="text-right hidden sm:block">
                  <div className="text-xs font-bold text-[#F5F5F5]">
                    {user?.full_name || user?.username || "Authorized User"}
                  </div>
                  <div className="text-[10px] text-[#FFD700] font-medium tracking-wide">
                    {roleDisplay}
                  </div>
                </div>
                <div className="w-8 h-8 rounded-full bg-[#FFD700] text-[#0B0B0D] font-bold text-xs flex items-center justify-center">
                  {(user?.full_name?.[0] || user?.username?.[0] || "U").toUpperCase()}
                </div>
              </button>

              {profileDropdownOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-[#17171B] border border-[#2A2A30] p-2 shadow-2xl z-50 text-xs animate-in fade-in zoom-in-95 duration-150">
                  <div className="px-3 py-2.5 border-b border-[#2A2A30]/80">
                    <p className="font-bold text-[#F5F5F5] truncate">{user?.full_name || user?.username}</p>
                    <p className="text-[11px] text-[#A1A1AA] truncate">{user?.email || "Connected via FastAPI"}</p>
                    <span className="inline-block mt-1 text-[10px] text-[#FFD700] font-semibold uppercase">
                      ● Role: {roleDisplay}
                    </span>
                  </div>

                  <Link
                    href={`/${role === "admin" ? "admin/settings" : role === "parent" ? "parent/profile" : role === "student" ? "student/profile" : "teacher"}`}
                    onClick={() => setProfileDropdownOpen(false)}
                    className="flex items-center gap-2 px-3 py-2 rounded-xl text-[#A1A1AA] hover:text-[#F5F5F5] hover:bg-[#111114] transition-colors mt-1"
                  >
                    <Settings className="w-3.5 h-3.5" />
                    <span>Workspace Settings</span>
                  </Link>

                  <button
                    type="button"
                    onClick={() => {
                      setProfileDropdownOpen(false);
                      logout();
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-red-400 hover:text-red-300 hover:bg-red-950/30 transition-colors"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content Body */}
        <main className="p-6 sm:p-8 flex-1">
          {/* Page Title & Actions Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F5F5F5] font-display tracking-tight">
                {title}
              </h1>
              {subtitle && <p className="text-xs sm:text-sm text-[#A1A1AA] mt-1">{subtitle}</p>}
            </div>
            {actions && <div className="flex items-center gap-3 shrink-0">{actions}</div>}
          </div>

          {/* Children View */}
          {children}
        </main>
      </div>
    </div>
  );
}
