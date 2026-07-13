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
        <div className="mt-3 flex items-center gap-2 text-xs text-slate-600">
          <span className="inline-flex h-3 w-3 animate-spin rounded-full border border-slate-300 border-t-orange-500" />
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
                    ? "border-orange-500 bg-orange-50 shadow-sm ring-1 ring-orange-500/30"
                    : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
                } ${disabled || loading ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${
                          selected
                            ? "border-orange-200 bg-orange-100 text-orange-700"
                            : "border-slate-200 bg-slate-100 text-slate-600 group-hover:text-slate-800"
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
                        <p className="truncate text-sm font-semibold text-slate-900">{label}</p>
                        <p className="truncate font-mono text-[11px] text-slate-600">
                          {account.account_id}
                        </p>
                      </div>
                    </div>
                  </div>
                  {selected && (
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-orange-600 text-[10px] font-bold text-white">
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
        <p className="mt-2.5 flex items-center gap-2 text-xs text-slate-600">
          <span className="inline-flex h-3 w-3 animate-spin rounded-full border border-slate-300 border-t-orange-500" />
          Refreshing accounts...
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
