"use client";

import type { ClusterItem } from "@/types/system";
import { ClusterSelector } from "@/components/ClusterSelector";

interface InvestigationFormProps {
  clusters: ClusterItem[];
  clusterId: string;
  onClusterChange: (clusterId: string) => void;
  onInvestigate: () => void;
  isLoading: boolean;
  disabled?: boolean;
  clustersLoading?: boolean;
  clustersError?: string | null;
}

export function InvestigationForm({
  clusters,
  clusterId,
  onClusterChange,
  onInvestigate,
  isLoading,
  disabled = false,
  clustersLoading = false,
  clustersError = null,
}: InvestigationFormProps) {
  return (
    <div className="panel-accent p-6">
      <div className="mb-5 flex items-center gap-3 border-b border-white/[0.06] pb-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-brand-500/20 bg-brand-500/10">
          <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 text-brand-300" aria-hidden>
            <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" />
            <path
              d="M12 2v3M12 19v3M2 12h3M19 12h3"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </div>
        <div>
          <h2 className="panel-title">Start Investigation</h2>
          <p className="text-xs text-slate-500">Select a cluster context to analyze</p>
        </div>
      </div>

      <div className="mb-5">
        <ClusterSelector
          clusters={clusters}
          clusterId={clusterId}
          onClusterChange={onClusterChange}
          disabled={disabled || isLoading}
          loading={clustersLoading}
          error={clustersError}
        />
      </div>

      <button
        type="button"
        onClick={onInvestigate}
        disabled={disabled || isLoading || !clusterId}
        className="btn-primary max-w-xs"
      >
        {isLoading ? (
          <span className="flex items-center gap-2">
            <span className="inline-flex h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            Investigating...
          </span>
        ) : (
          "Investigate Cluster"
        )}
      </button>
    </div>
  );
}
