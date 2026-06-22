"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export function RedirectIfAuthenticated({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading || isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-400">
        <span className="inline-flex h-5 w-5 animate-spin rounded-full border-2 border-slate-600 border-t-brand-400" />
      </div>
    );
  }

  return <>{children}</>;
}
