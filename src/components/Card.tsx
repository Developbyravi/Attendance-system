import { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  /** Elevation level matching Stitch depth system */
  level?: 0 | 1 | 2;
  padding?: string;
}

const SHADOWS: Record<number, string> = {
  0: "",
  1: "shadow-card",
  2: "shadow-card-md",
};

export default function Card({
  children,
  className = "",
  level = 1,
  padding = "p-space-md",
}: CardProps) {
  return (
    <div
      className={`bg-surface-container-lowest rounded-xl border border-transparent ${SHADOWS[level]} ${padding} ${className}`}
    >
      {children}
    </div>
  );
}
