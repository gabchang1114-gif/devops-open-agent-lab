"use client";

import type { ClusterItem } from "@/types/system";

interface ClusterSelectorProps {
  clusters: ClusterItem[];
  clusterId: string;
  onClusterChange: (clusterId: string) => void;
  disabled?: boolean;
  loading?: boolean;
  error?: string | null;
  label?: string;
  compact?: boolean;
}

export function ClusterSelector({
  clusters,
  clusterId,
  onClusterChange,
  disabled = false,
  loading = false,
  error = null,
  label = "Select Cluster",
  compact = false,
}: ClusterSelectorProps) {
  const options =
    clusters.length > 0
      ? clusters
      : clusterId
        ? [
            {
              cluster_id: clusterId,
              context: clusterId,
              name: clusterId,
              active: true,
            },
          ]
        : [];

  return (
    <div>
      <p className="section-label">{label}</p>

      {loading && options.length === 0 ? (
        <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
          <span className="inline-flex h-3 w-3 animate-spin rounded-full border border-slate-600 border-t-slate-400" />
          Loading clusters from kubeconfig...
        </div>
      ) : (
        <div
          role="radiogroup"
          aria-label={label}
          className={`mt-3 grid gap-3 ${
            compact ? "grid-cols-2 sm:grid-cols-3 lg:grid-cols-4" : "grid-cols-1 sm:grid-cols-2"
          }`}
        >
          {options.map((cluster) => {
            const selected = clusterId === cluster.cluster_id;
            return (
              <button
                key={cluster.cluster_id}
                type="button"
                role="radio"
                aria-checked={selected}
                disabled={disabled || loading}
                onClick={() => onClusterChange(cluster.cluster_id)}
                className={`group relative rounded-xl border px-4 py-3 text-left transition ${
                  selected
                    ? "border-brand-500/50 bg-brand-500/10 shadow-[0_0_0_1px_rgba(59,130,246,0.25)]"
                    : "border-white/[0.08] bg-slate-950/40 hover:border-white/[0.14] hover:bg-slate-900/60"
                } ${disabled || loading ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${
                          selected
                            ? "border-brand-500/30 bg-brand-500/15 text-brand-300"
                            : "border-white/[0.08] bg-slate-900/70 text-slate-400 group-hover:text-slate-300"
                        }`}
                      >
                        <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" aria-hidden>
                          <path
                            d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </span>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-white">{cluster.name}</p>
                        {!compact && (
                          <p className="truncate font-mono text-[11px] text-slate-500">
                            {cluster.context}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {selected && (
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-500 text-[10px] font-bold text-white">
                      ✓
                    </span>
                  )}
                </div>

                {cluster.active && (
                  <span className="mt-3 inline-flex rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-emerald-200">
                    Active context
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {loading && options.length > 0 && (
        <p className="mt-2.5 flex items-center gap-2 text-xs text-slate-500">
          <span className="inline-flex h-3 w-3 animate-spin rounded-full border border-slate-600 border-t-slate-400" />
          Refreshing clusters...
        </p>
      )}

      {error && (
        <p className="mt-2.5 whitespace-pre-line rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
          {error}
        </p>
      )}
    </div>
  );
}
