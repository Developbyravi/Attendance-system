import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AuthProvider } from "@/context/AuthContext";
import "./globals.css";

export const metadata: Metadata = {
  title: "AIoT SmartAttend — Intelligent Attendance Management System",
  description:
    "SmartAttend combines RFID daily check-in with AI-assisted classroom verification for educational institutions. Smarter Attendance. Verified by AI.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className="bg-dark-bg text-brand-text antialiased min-h-screen selection:bg-gold/30 selection:text-gold"
        suppressHydrationWarning
      >
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
