"use client";

import type { AwsAccountSummary, AwsIssueType, AwsRegionInfo, CloudWatchWindow } from "@/types/aws";
import { AwsAccountSelector } from "@/components/aws/AwsAccountSelector";
import { AWS_ISSUE_TYPES } from "@/lib/awsIssueTypes";

const CLOUDWATCH_WINDOWS: { value: CloudWatchWindow; label: string }[] = [
  { value: "1h", label: "Last 1 hour" },
  { value: "24h", label: "Last 24 hours" },
  { value: "7d", label: "Last 7 days" },
];

const SUPPORTED_AWS_SERVICES = [
  "EC2",
  "Lambda",
  "S3",
  "VPC",
  "Security Groups",
  "Load Balancers",
  "Auto Scaling",
  "CloudWatch",
  "CloudTrail",
] as const;

interface AwsInvestigationFormProps {
  accounts: AwsAccountSummary[];
  accountId: string;
  onAccountChange: (accountId: string) => void;
  regions: AwsRegionInfo[];
  region: string;
  onRegionChange: (region: string) => void;
  issueType: AwsIssueType;
  onIssueTypeChange: (issueType: AwsIssueType) => void;
  query: string;
  onQueryChange: (query: string) => void;
  cloudwatchWindow: CloudWatchWindow;
  onCloudwatchWindowChange: (window: CloudWatchWindow) => void;
  onInvestigate: () => void;
  isLoading: boolean;
  disabled?: boolean;
  accountsLoading?: boolean;
  accountsError?: string | null;
  regionsLoading?: boolean;
  regionsError?: string | null;
}

export function AwsInvestigationForm({
  accounts,
  accountId,
  onAccountChange,
  regions,
  region,
  onRegionChange,
  issueType,
  onIssueTypeChange,
  query,
  onQueryChange,
  cloudwatchWindow,
  onCloudwatchWindowChange,
  onInvestigate,
  isLoading,
  disabled = false,
  accountsLoading = false,
  accountsError = null,
  regionsLoading = false,
  regionsError = null,
}: AwsInvestigationFormProps) {
  return (
    <div className="panel-accent p-6">
      <div className="mb-5 flex items-center gap-3 border-b border-white/[0.06] pb-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-orange-500/20 bg-orange-500/10">
          <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 text-orange-300" aria-hidden>
            <path
              d="M12 2L4 6v6c0 5 3.5 9.5 8 11 4.5-1.5 8-6 8-11V6l-8-4z"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <div>
          <h2 className="panel-title">Troubleshoot AWS Infrastructure</h2>
          <p className="text-xs text-slate-500">
            Discover EC2, Lambda, S3, networking, and load balancers — then run AI analysis
          </p>
        </div>
      </div>

      <div className="mb-5">
        <p className="section-label">Supported Services</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {SUPPORTED_AWS_SERVICES.map((service) => (
            <span
              key={service}
              className="rounded-full border border-orange-500/20 bg-orange-500/10 px-3 py-1 text-[11px] font-medium text-orange-200"
            >
              {service}
            </span>
          ))}
        </div>
      </div>

      <div className="mb-5">
        <AwsAccountSelector
          accounts={accounts}
          accountId={accountId}
          onAccountChange={onAccountChange}
          disabled={disabled || isLoading}
          loading={accountsLoading}
          error={accountsError}
        />
      </div>

      {accountId && (
        <div className="mb-5">
          <p className="section-label">Select Region</p>
          {regionsLoading && regions.length === 0 ? (
            <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
              <span className="inline-flex h-3 w-3 animate-spin rounded-full border border-slate-600 border-t-slate-400" />
              Loading regions...
            </div>
          ) : (
            <div className="mt-3 flex flex-wrap gap-2">
              {regions.map((item) => {
                const selected = region === item.region;
                return (
                  <button
                    key={item.region}
                    type="button"
                    disabled={disabled || isLoading}
                    onClick={() => onRegionChange(item.region)}
                    className={`rounded-lg border px-3 py-1.5 font-mono text-xs transition ${
                      selected
                        ? "border-orange-500/50 bg-orange-500/15 text-orange-200"
                        : "border-white/[0.08] bg-slate-950/40 text-slate-400 hover:border-white/[0.14] hover:text-slate-200"
                    } ${disabled || isLoading ? "cursor-not-allowed opacity-60" : ""}`}
                  >
                    {item.region}
                  </button>
                );
              })}
            </div>
          )}
          {regionsError && (
            <p className="mt-2.5 rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
              {regionsError}
            </p>
          )}
        </div>
      )}

      <div className="mb-5">
        <p className="section-label">What do you want to troubleshoot?</p>
        <div
          role="radiogroup"
          aria-label="Issue type"
          className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2"
        >
          {AWS_ISSUE_TYPES.map((item) => {
            const selected = issueType === item.value;
            return (
              <button
                key={item.value}
                type="button"
                role="radio"
                aria-checked={selected}
                disabled={disabled || isLoading}
                onClick={() => onIssueTypeChange(item.value)}
                className={`rounded-xl border px-4 py-3 text-left transition ${
                  selected
                    ? "border-orange-500/50 bg-orange-500/10 shadow-[0_0_0_1px_rgba(249,115,22,0.25)]"
                    : "border-white/[0.08] bg-slate-950/40 hover:border-white/[0.14] hover:bg-slate-900/60"
                } ${disabled || isLoading ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
              >
                <p className="text-sm font-semibold text-white">{item.label}</p>
                <p className="mt-1 text-xs leading-relaxed text-slate-500">{item.description}</p>
              </button>
            );
          })}
        </div>
      </div>

      <div className="mb-5">
        <label htmlFor="aws-issue-query" className="section-label">
          Describe the issue (optional)
        </label>
        <textarea
          id="aws-issue-query"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          disabled={disabled || isLoading}
          placeholder="e.g. I opened HTTP to the internet on a security group and want to know if it's exposed..."
          rows={3}
          className="mt-3 w-full rounded-xl border border-white/[0.08] bg-slate-950/40 px-4 py-3 text-sm text-slate-200 placeholder:text-slate-600 focus:border-orange-500/40 focus:outline-none"
        />
      </div>

      <div className="mb-5">
        <p className="section-label">Evidence Window</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {CLOUDWATCH_WINDOWS.map((item) => {
            const selected = cloudwatchWindow === item.value;
            return (
              <button
                key={item.value}
                type="button"
                disabled={disabled || isLoading}
                onClick={() => onCloudwatchWindowChange(item.value)}
                className={`rounded-lg border px-3 py-1.5 text-xs transition ${
                  selected
                    ? "border-brand-500/50 bg-brand-500/15 text-brand-200"
                    : "border-white/[0.08] bg-slate-950/40 text-slate-400 hover:border-white/[0.14] hover:text-slate-200"
                } ${disabled || isLoading ? "cursor-not-allowed opacity-60" : ""}`}
              >
                {item.label}
              </button>
            );
          })}
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Applies to CloudWatch metrics and CloudTrail lookback
        </p>
      </div>

      <button
        type="button"
        onClick={onInvestigate}
        disabled={disabled || isLoading || !accountId || !region}
        className="btn-primary max-w-xs"
      >
        {isLoading ? (
          <span className="flex items-center gap-2">
            <span className="inline-flex h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            Troubleshooting...
          </span>
        ) : (
          "Troubleshoot"
        )}
      </button>
    </div>
  );
}
