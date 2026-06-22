"use client";

import type { AwsAccountSummary } from "@/types/aws";

interface AwsAccountSelectorProps {
  accounts: AwsAccountSummary[];
  accountId: string;
  onAccountChange: (accountId: string) => void;
  disabled?: boolean;
  loading?: boolean;
  error?: string | null;
}

export function AwsAccountSelector({
  accounts,
  accountId,
  onAccountChange,
  disabled = false,
  loading = false,
  error = null,
}: AwsAccountSelectorProps) {
  const options =
    accounts.length > 0
      ? accounts
      : accountId
        ? [{ account_id: accountId, account_name: accountId }]
        : [];

  return (
    <div>
      <p className="section-label">Select AWS Account</p>

      {loading && options.length === 0 ? (
        <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
          <span className="inline-flex h-3 w-3 animate-spin rounded-full border border-slate-600 border-t-slate-400" />
          Discovering AWS accounts...
        </div>
      ) : (
        <div
          role="radiogroup"
          aria-label="Select AWS Account"
          className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2"
        >
          {options.map((account) => {
            const selected = accountId === account.account_id;
            const label = account.account_name ?? account.account_id;
            return (
              <button
                key={account.account_id}
                type="button"
                role="radio"
                aria-checked={selected}
                disabled={disabled || loading}
                onClick={() => onAccountChange(account.account_id)}
                className={`group relative rounded-xl border px-4 py-3 text-left transition ${
                  selected
                    ? "border-orange-500/50 bg-orange-500/10 shadow-[0_0_0_1px_rgba(249,115,22,0.25)]"
                    : "border-white/[0.08] bg-slate-950/40 hover:border-white/[0.14] hover:bg-slate-900/60"
                } ${disabled || loading ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${
                          selected
                            ? "border-orange-500/30 bg-orange-500/15 text-orange-300"
                            : "border-white/[0.08] bg-slate-900/70 text-slate-400 group-hover:text-slate-300"
                        }`}
                      >
                        <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" aria-hidden>
                          <path
                            d="M12 2L4 6v6c0 5 3.5 9.5 8 11 4.5-1.5 8-6 8-11V6l-8-4z"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </span>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-white">{label}</p>
                        <p className="truncate font-mono text-[11px] text-slate-500">
                          {account.account_id}
                        </p>
                      </div>
                    </div>
                  </div>
                  {selected && (
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-orange-500 text-[10px] font-bold text-white">
                      ✓
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}

      {loading && options.length > 0 && (
        <p className="mt-2.5 flex items-center gap-2 text-xs text-slate-500">
          <span className="inline-flex h-3 w-3 animate-spin rounded-full border border-slate-600 border-t-slate-400" />
          Refreshing accounts...
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
