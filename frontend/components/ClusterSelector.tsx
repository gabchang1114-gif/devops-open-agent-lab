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
        <div className="mt-3 flex items-center gap-2 text-xs text-slate-600">
          <span className="inline-flex h-3 w-3 animate-spin rounded-full border border-slate-300 border-t-brand-500" />
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
                    ? "border-brand-500 bg-brand-50 shadow-sm ring-1 ring-brand-500/30"
                    : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
                } ${disabled || loading ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${
                          selected
                            ? "border-brand-200 bg-brand-100 text-brand-700"
                            : "border-slate-200 bg-slate-100 text-slate-600 group-hover:text-slate-800"
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
                        <p className="truncate text-sm font-semibold text-slate-900">
                          {cluster.name}
                        </p>
                        {!compact && (
                          <p className="truncate font-mono text-[11px] text-slate-600">
                            {cluster.context}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {selected && (
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-600 text-[10px] font-bold text-white">
                      ✓
                    </span>
                  )}
                </div>

                {cluster.active && (
                  <span className="mt-3 inline-flex rounded-full border border-emerald-300 bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-800">
                    Active context
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {loading && options.length > 0 && (
        <p className="mt-2.5 flex items-center gap-2 text-xs text-slate-600">
          <span className="inline-flex h-3 w-3 animate-spin rounded-full border border-slate-300 border-t-brand-500" />
          Refreshing clusters...
        </p>
      )}

      {error && (
        <p className="mt-2.5 whitespace-pre-line rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-900">
          {error}
        </p>
      )}
    </div>
  );
}
