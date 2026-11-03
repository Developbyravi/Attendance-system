import React, { type ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon?: React.ComponentType<{ className?: string }>;
  trend?: string;
  trendPositive?: boolean;
  className?: string;
}

export default function StatCard({
  label,
  value,
  subtext,
  icon: IconComponent,
  trend,
  trendPositive = true,
  className = "",
}: StatCardProps) {
  return (
    <div
      className={`bg-[#17171B] border border-[#2A2A30] hover:border-[#C9A227]/40 rounded-2xl p-5 flex flex-col justify-between transition-all ${className}`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] font-semibold text-[#A1A1AA] uppercase tracking-wider">
          {label}
        </span>
        {IconComponent && (
          <div className="w-8 h-8 rounded-xl bg-[#111114] border border-[#2A2A30] text-[#FFD700] flex items-center justify-center">
            <IconComponent className="w-4 h-4" />
          </div>
        )}
      </div>

      <div>
        <div className="text-2xl sm:text-3xl font-extrabold text-[#F5F5F5] tracking-tight tabular-nums font-sans">
          {value}
        </div>
        {(subtext || trend) && (
          <div className="flex items-center gap-1.5 mt-2 text-xs">
            {trend && (
              <span
                className={`font-semibold ${
                  trendPositive ? "text-[#7BD88F]" : "text-red-400"
                }`}
              >
                {trend}
              </span>
            )}
            {subtext && <span className="text-[#A1A1AA] truncate">{subtext}</span>}
          </div>
        )}
      </div>
    </div>
  );
}
