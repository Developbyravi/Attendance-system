import React, { type ReactNode } from "react";
import { Inbox } from "lucide-react";

interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export default function EmptyState({
  icon: IconComponent = Inbox,
  title,
  description,
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`bg-[#17171B] border border-[#2A2A30] rounded-2xl p-8 sm:p-12 text-center flex flex-col items-center justify-center ${className}`}
    >
      <div className="w-14 h-14 rounded-2xl bg-[#111114] border border-[#2A2A30] text-[#FFD700] flex items-center justify-center mb-4 shadow-[0_0_20px_rgba(255,215,0,0.06)]">
        <IconComponent className="w-7 h-7" />
      </div>
      <h3 className="text-base sm:text-lg font-bold text-[#F5F5F5] mb-1.5">{title}</h3>
      {description && (
        <p className="text-xs sm:text-sm text-[#A1A1AA] max-w-md mx-auto leading-relaxed mb-6">
          {description}
        </p>
      )}
      {action && <div>{action}</div>}
    </div>
  );
}
