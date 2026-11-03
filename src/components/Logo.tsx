import React from "react";
import Link from "next/link";

interface LogoProps {
  className?: string;
  showText?: boolean;
  size?: "sm" | "md" | "lg";
  height?: number;
  href?: string;
}

export default function Logo({
  className = "",
  showText = true,
  size = "md",
  height,
  href,
}: LogoProps) {
  const iconSizes = {
    sm: "w-6 h-6",
    md: "w-7 h-7",
    lg: "w-9 h-9",
  };

  const textSizes = {
    sm: "text-base",
    md: "text-lg",
    lg: "text-2xl",
  };

  const content = (
    <div
      className={`inline-flex items-center gap-2.5 font-sans font-bold tracking-tight select-none ${className}`}
      style={height ? { height } : undefined}
    >
      <div className={`relative flex items-center justify-center ${iconSizes[size]}`}>
        <svg
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full drop-shadow-[0_0_8px_rgba(255,215,0,0.35)]"
        >
          {/* Hexagonal Shield */}
          <path
            d="M16 3L27 9V17C27 23.5 16 29 16 29C16 29 5 23.5 5 17V9L16 3Z"
            stroke="#FFD700"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="fill-gold/10"
          />
          {/* Verified Check / Core Mark */}
          <path
            d="M11 16L14.5 19.5L21.5 12.5"
            stroke="#FFD700"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      {showText && (
        <span className={`font-semibold tracking-tight text-brand-text ${textSizes[size]}`}>
          Smart<span className="text-gold">Attend</span>
        </span>
      )}
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="hover:opacity-95 transition-opacity inline-flex">
        {content}
      </Link>
    );
  }

  return content;
}
