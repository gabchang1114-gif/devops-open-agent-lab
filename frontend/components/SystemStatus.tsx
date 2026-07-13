"use client";

import { useReadiness } from "@/hooks/useClusters";

interface SystemStatusProps {
  variant?: "default" | "sidebar";
}

export function SystemStatus({ variant = "default" }: SystemStatusProps) {
  const { data, isLoading, isError } = useReadiness();
  const compact = variant === "sidebar";

  if (isLoading) {
    return (
      <div
        className={`flex items-center gap-2 text-sm ${
          compact ? "text-slate-400" : "text-slate-600"
        }`}
      >
        <span className="inline-flex h-3.5 w-3.5 animate-spin rounded-full border-2 border-slate-500 border-t-brand-400" />
        <span className="text-xs">Checking readiness...</span>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <span className="relative flex h-2 w-2">
          <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500" />
        </span>
        <span className={`text-xs ${compact ? "text-red-300" : "text-red-600"}`}>
          Backend unavailable
        </span>
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
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="relative flex h-2 w-2">
          {allReady && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/40" />
          )}
          <span
            className={`relative inline-flex h-2 w-2 rounded-full ${
              allReady ? "bg-emerald-500" : "bg-amber-400"
            }`}
          />
        </span>
        <span className={`text-xs font-medium ${compact ? "text-slate-300" : "text-slate-700"}`}>
          {allReady ? "All systems ready" : "Needs attention"}
        </span>
      </div>

      <div className="flex flex-wrap gap-1">
        {checks.map((check) => (
          <span
            key={check.label}
            className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-medium ${
              check.ok
                ? compact
                  ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-300"
                  : "border-emerald-200 bg-emerald-50 text-emerald-700"
                : compact
                  ? "border-amber-500/25 bg-amber-500/10 text-amber-200"
                  : "border-amber-200 bg-amber-50 text-amber-700"
            }`}
          >
            <span
              className={`h-1 w-1 rounded-full ${check.ok ? "bg-emerald-400" : "bg-amber-400"}`}
            />
            {check.label}
          </span>
        ))}
      </div>
    </div>
  );
}
