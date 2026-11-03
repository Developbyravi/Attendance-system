import React from "react";

export type AttendanceStatus =
  | "present"
  | "absent"
  | "flagged"
  | "review"
  | "verified"
  | "finalized"
  | "pending"
  | "online"
  | "offline";

const STATUS_MAP: Record<
  AttendanceStatus,
  { label: string; textClass: string; bgClass: string; borderClass: string; dotClass: string }
> = {
  present:   { label: "Present",      textClass: "text-[#7BD88F]", bgClass: "bg-emerald-950/40", borderClass: "border-emerald-700/40", dotClass: "bg-[#7BD88F]" },
  verified:  { label: "Verified",     textClass: "text-[#7BD88F]", bgClass: "bg-emerald-950/40", borderClass: "border-emerald-700/40", dotClass: "bg-[#7BD88F]" },
  absent:    { label: "Absent",       textClass: "text-red-400",   bgClass: "bg-red-950/40",     borderClass: "border-red-700/40",     dotClass: "bg-red-400" },
  flagged:   { label: "Flagged",      textClass: "text-[#FFD700]", bgClass: "bg-amber-950/40",   borderClass: "border-amber-700/40",   dotClass: "bg-[#FFD700]" },
  review:    { label: "Needs Review", textClass: "text-[#FFD700]", bgClass: "bg-amber-950/40",   borderClass: "border-amber-700/40",   dotClass: "bg-[#FFD700]" },
  finalized: { label: "Finalized",    textClass: "text-[#F5F5F5]", bgClass: "bg-[#17171B]",      borderClass: "border-[#2A2A30]",       dotClass: "bg-[#A1A1AA]" },
  pending:   { label: "Pending",      textClass: "text-[#A1A1AA]", bgClass: "bg-[#17171B]",      borderClass: "border-[#2A2A30]",       dotClass: "bg-[#A1A1AA]" },
  online:    { label: "Online",       textClass: "text-[#7BD88F]", bgClass: "bg-emerald-950/40", borderClass: "border-emerald-700/40", dotClass: "bg-[#7BD88F]" },
  offline:   { label: "Offline",      textClass: "text-zinc-400",  bgClass: "bg-zinc-900",       borderClass: "border-zinc-800",        dotClass: "bg-zinc-500" },
};

interface StatusBadgeProps {
  status: string;
  className?: string;
  labelOverride?: string;
}

export default function StatusBadge({ status, className = "", labelOverride }: StatusBadgeProps) {
  const normalized = (status?.toLowerCase() || "pending") as AttendanceStatus;
  const config = STATUS_MAP[normalized] || STATUS_MAP.pending;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${config.textClass} ${config.bgClass} ${config.borderClass} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dotClass}`} />
      <span>{labelOverride || config.label}</span>
    </span>
  );
}
