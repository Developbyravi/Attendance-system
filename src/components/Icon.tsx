"use client";

interface IconProps {
  name: string;
  className?: string;
  filled?: boolean;
  size?: number;
}

/**
 * Wrapper for Material Symbols Outlined.
 * `filled` sets FILL=1 via font-variation-settings.
 */
export default function Icon({ name, className = "", filled = false, size = 22 }: IconProps) {
  return (
    <span
      className={`material-symbols-outlined select-none leading-none ${className}`}
      style={{
        fontSize: size,
        fontVariationSettings: filled
          ? `'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24`
          : `'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24`,
      }}
      aria-hidden="true"
    >
      {name}
    </span>
  );
}
