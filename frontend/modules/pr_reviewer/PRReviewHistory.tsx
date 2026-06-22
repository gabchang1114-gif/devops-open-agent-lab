"use client";

import Link from "next/link";
import type { PrReviewHistoryItem } from "@/types/prReviewer";

function riskBadgeClass(risk?: string | null): string {
  switch (risk?.toLowerCase()) {
    case "high":
      return "border-red-500/30 bg-red-500/10 text-red-300";
    case "medium":
      return "border-amber-500/30 bg-amber-500/10 text-amber-300";
    case "low":
      return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
    default:
      return "border-white/[0.08] bg-white/[0.03] text-slate-400";
  }
}

function statusBadgeClass(status: string): string {
  if (status === "completed") {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
  }
  if (status === "failed") {
    return "border-red-500/30 bg-red-500/10 text-red-300";
  }
  return "border-brand-500/30 bg-brand-500/10 text-brand-200";
}

function formatRecommendation(value?: string | null): string {
  if (!value) return "—";
  return value.replace(/_/g, " ");
}

interface PRReviewHistoryProps {
  reviews: PrReviewHistoryItem[];
  isLoading?: boolean;
  title?: string;
  subtitle?: string;
  emptyStateHref?: string;
  emptyStateLabel?: string;
  detailBasePath?: string;
}

export function PRReviewHistory({
  reviews,
  isLoading,
  title = "Recent Reviews",
  subtitle,
  emptyStateHref = "/pr-reviewer",
  emptyStateLabel = "Run your first PR review",
  detailBasePath = "/pr-reviewer/reviews",
}: PRReviewHistoryProps) {
  if (isLoading) {
    return (
      <section className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-6">
        <h2 className="text-lg font-semibold text-white">{title}</h2>
        <p className="mt-4 text-sm text-slate-400">Loading review history...</p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-6">
      <div className="mb-5 flex items-center justify-between gap-4 border-b border-white/[0.06] pb-4">
        <div>
          {subtitle && <p className="mb-1 text-xs uppercase tracking-wide text-slate-500">{subtitle}</p>}
          <h2 className="text-lg font-semibold text-white">{title}</h2>
        </div>
        {reviews.length > 0 && (
          <span className="rounded-full border border-white/[0.08] bg-slate-800/60 px-3 py-1 text-xs font-medium tabular-nums text-slate-400">
            {reviews.length} total
          </span>
        )}
      </div>

      {reviews.length === 0 ? (
        <div className="text-sm text-slate-400">
          <p>No PR reviews yet.</p>
          <Link href={emptyStateHref} className="mt-2 inline-block text-brand-200 hover:underline">
            {emptyStateLabel}
          </Link>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-slate-400">
              <tr className="border-b border-white/[0.08]">
                <th className="px-3 py-2 font-medium">Repository</th>
                <th className="px-3 py-2 font-medium">PR</th>
                <th className="px-3 py-2 font-medium">Title</th>
                <th className="px-3 py-2 font-medium">Risk</th>
                <th className="px-3 py-2 font-medium">Findings</th>
                <th className="px-3 py-2 font-medium">Recommendation</th>
                <th className="px-3 py-2 font-medium">Status</th>
                <th className="px-3 py-2 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {reviews.map((review) => (
                <tr key={review.id} className="border-b border-white/[0.05] text-slate-200">
                  <td className="px-3 py-3 font-mono text-xs">
                    <Link
                      href={`${detailBasePath}/${review.id}?from=${encodeURIComponent("/pr-reviewer/investigations")}`}
                      className="text-brand-200 hover:underline"
                    >
                      {review.owner}/{review.repository}
                    </Link>
                  </td>
                  <td className="px-3 py-3">#{review.pull_request_number}</td>
                  <td className="max-w-xs truncate px-3 py-3">
                    {review.pull_request_title || "—"}
                  </td>
                  <td className="px-3 py-3">
                    <span
                      className={`inline-flex rounded-full border px-2 py-0.5 text-xs capitalize ${riskBadgeClass(review.overall_risk)}`}
                    >
                      {review.overall_risk || "—"}
                    </span>
                  </td>
                  <td className="px-3 py-3">{review.findings_count}</td>
                  <td className="px-3 py-3 capitalize">
                    {formatRecommendation(review.final_recommendation)}
                  </td>
                  <td className="px-3 py-3">
                    <span
                      className={`inline-flex rounded-full border px-2 py-0.5 text-xs capitalize ${statusBadgeClass(review.status)}`}
                    >
                      {review.status}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-xs text-slate-400">
                    {new Date(review.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
