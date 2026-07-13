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
  includeRag?: boolean;
  onIncludeRagChange?: (value: boolean) => void;
  ragAvailable?: boolean;
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
  includeRag = false,
  onIncludeRagChange,
  ragAvailable = false,
}: InvestigationFormProps) {
  return (
    <div className="panel-accent p-6">
      <div className="mb-5 flex items-center gap-3 border-b border-slate-200 pb-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-brand-200 bg-brand-50">
          <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 text-brand-700" aria-hidden>
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
          <p className="text-xs text-slate-600">Select a cluster context to analyze</p>
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

      {ragAvailable && (
        <label className="mb-5 flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
          <input
            type="checkbox"
            checked={includeRag}
            disabled={disabled || isLoading}
            onChange={(event) => onIncludeRagChange?.(event.target.checked)}
            className="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
          />
          <span>
            <span className="block text-sm font-medium text-slate-900">
              Include past investigations (RAG)
            </span>
            <span className="mt-0.5 block text-xs text-slate-600">
              Retrieve similar prior investigations from Qdrant and factor them into the AI
              analysis.
            </span>
          </span>
        </label>
      )}

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
