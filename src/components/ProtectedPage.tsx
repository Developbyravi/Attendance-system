"use client";

import { useEffect, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import type { UserRole } from "@/types/auth";
import Logo from "@/components/Logo";
import { Loader2 } from "lucide-react";

interface ProtectedPageProps {
  requiredRole: UserRole;
  children: ReactNode;
}

export default function ProtectedPage({ requiredRole, children }: ProtectedPageProps) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }
    if (user) {
      const uRole = String(user.role).toLowerCase();
      const rRole = String(requiredRole).toLowerCase();
      if (uRole !== rRole && uRole !== "admin") {
        router.replace("/unauthorized");
      }
    }
  }, [isLoading, isAuthenticated, user, requiredRole, router]);

  const hasAccess = user
    ? String(user.role).toLowerCase() === String(requiredRole).toLowerCase() || String(user.role).toLowerCase() === "admin"
    : false;

  if (isLoading || !isAuthenticated || !hasAccess) {
    return (
      <div className="min-h-screen bg-[#0B0B0D] flex flex-col items-center justify-center gap-4 text-[#A1A1AA]">
        <Logo size="lg" />
        <div className="flex items-center gap-2 text-xs">
          <Loader2 className="w-4 h-4 animate-spin text-[#FFD700]" />
          <span>Verifying security permissions...</span>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
