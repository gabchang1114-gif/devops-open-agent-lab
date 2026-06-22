"use client";

interface CloudCostDetectorFormProps {
  accountId: string;
  accountName?: string | null;
  region: string;
  regions: string[];
  onRegionChange: (region: string) => void;
  onAnalyze: () => void;
  isLoading: boolean;
  accountLoading?: boolean;
  regionsLoading?: boolean;
  accountError?: string | null;
  regionsError?: string | null;
}

export function CloudCostDetectorForm({
  accountId,
  accountName,
  region,
  regions,
  onRegionChange,
  onAnalyze,
  isLoading,
  accountLoading = false,
  regionsLoading = false,
  accountError = null,
  regionsError = null,
}: CloudCostDetectorFormProps) {
  return (
    <div className="panel-accent p-6">
      <div className="mb-5 flex items-center gap-3 border-b border-white/[0.06] pb-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-emerald-500/20 bg-emerald-500/10">
          <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 text-emerald-300" aria-hidden>
            <path
              d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <div>
          <h2 className="panel-title">Cloud Cost Detector</h2>
          <p className="text-xs text-slate-500">AWS Cost Optimization Platform</p>
        </div>
      </div>

      {(accountError || regionsError) && (
        <div className="alert-error mb-4 text-sm">
          {accountError || regionsError}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="ccd-account" className="section-label">
            Account
          </label>
          <div
            id="ccd-account"
            className="input-field flex min-h-[42px] items-center font-mono text-sm text-slate-300"
          >
            {accountLoading ? (
              <span className="text-slate-500">Loading account...</span>
            ) : (
              <>
                {accountName ? `${accountName} · ` : ""}
                {accountId || "—"}
              </>
            )}
          </div>
        </div>

        <div>
          <label htmlFor="ccd-region" className="section-label">
            Region
          </label>
          <select
            id="ccd-region"
            value={region}
            onChange={(event) => onRegionChange(event.target.value)}
            className="input-field w-full"
            disabled={regionsLoading || regions.length === 0}
          >
            {regions.map((regionName) => (
              <option key={regionName} value={regionName}>
                {regionName}
              </option>
            ))}
          </select>
        </div>
      </div>

      <button
        type="button"
        onClick={onAnalyze}
        disabled={isLoading || !accountId || !region}
        className="btn-primary mt-5 min-w-[180px] bg-emerald-600 hover:bg-emerald-500"
      >
        {isLoading ? "Analyzing..." : "Analyze Resources"}
      </button>
    </div>
  );
}
