import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // AIoT SmartAttend Official Palette
        dark: {
          bg: "#0B0B0D",
          surface: "#111114",
          card: "#17171B",
          cardHover: "#1F1F24",
          border: "#2A2A30",
          borderLight: "#3A3A42",
        },
        gold: {
          DEFAULT: "#FFD700",
          secondary: "#C9A227",
          dark: "#A38018",
          glow: "rgba(255, 215, 0, 0.15)",
        },
        brand: {
          text: "#F5F5F5",
          muted: "#A1A1AA",
          dim: "#71717A",
        },
        status: {
          success: "#22C55E",
          warning: "#F59E0B",
          error: "#EF4444",
          info: "#3B82F6",
        },
      },
      borderRadius: {
        xl: "14px",
        "2xl": "18px",
        "3xl": "24px",
      },
      fontFamily: {
        sans: ["Plus Jakarta Sans", "Inter", "system-ui", "sans-serif"],
        display: ["Bricolage Grotesque", "Plus Jakarta Sans", "sans-serif"],
      },
      boxShadow: {
        goldGlow: "0 0 25px rgba(255, 215, 0, 0.25)",
        darkCard: "0 8px 32px -4px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.04) inset",
      },
    },
  },
  plugins: [],
};

export default config;
