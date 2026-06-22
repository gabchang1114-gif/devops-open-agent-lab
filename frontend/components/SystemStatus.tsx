"use client";

import { useReadiness } from "@/hooks/useClusters";

export function SystemStatus() {
  const { data, isLoading, isError } = useReadiness();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2.5 text-sm text-slate-400">
        <span className="inline-flex h-4 w-4 animate-spin rounded-full border-2 border-slate-600 border-t-brand-400" />
        Checking system readiness...
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex items-center gap-2.5 text-sm">
        <span className="relative flex h-2.5 w-2.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400/40" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500" />
        </span>
        <span className="text-red-300">System Status: Backend unavailable</span>
      </div>
    );
  }

  const checks = [
    { label: "kubectl", ok: data.kubectl },
    { label: "kubeconfig", ok: data.kubeconfig },
    { label: "cluster", ok: data.cluster_reachable },
    { label: "LLM", ok: data.llm_provider },
    { label: "database", ok: data.database },
  ];
  const allReady = checks.every((check) => check.ok);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2.5">
        <span className="relative flex h-2.5 w-2.5">
          {allReady && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/30" />
          )}
          <span
            className={`relative inline-flex h-2.5 w-2.5 rounded-full ${
              allReady ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" : "bg-amber-400"
            }`}
          />
        </span>
        <div className="text-sm text-slate-300">
          <span className="text-slate-500">System Status</span>
          <span className="mx-1.5 text-slate-600">·</span>
          <span className={allReady ? "font-semibold text-emerald-400" : "font-semibold text-amber-300"}>
            {allReady ? "Ready" : "Needs Attention"}
          </span>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {checks.map((check) => (
          <span
            key={check.label}
            className={`status-pill ${
              check.ok
                ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
                : "border-amber-500/20 bg-amber-500/10 text-amber-200"
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                check.ok ? "bg-emerald-400" : "bg-amber-400"
              }`}
            />
            {check.label}: {check.ok ? "ok" : "missing"}
          </span>
        ))}
      </div>
    </div>
  );
}
