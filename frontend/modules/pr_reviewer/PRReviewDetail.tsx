"use client";

import type { PrReviewDetail } from "@/types/prReviewer";
import { PrReviewMcpPanel } from "@/modules/pr_reviewer/PrReviewMcpPanel";

interface PRReviewDetailProps {
  review: PrReviewDetail;
}

const REVIEW_STEP_LABELS: Record<string, string> = {
  queued: "Queued",
  fetching_pr_files: "Fetching PR files",
  building_prompt: "Building review prompt",
  discovering_mcp: "Discovering MCP tools",
  running_ai_review: "Running AI review",
  posting_github_comment: "Posting GitHub comment",
  completed: "Completed",
};

function formatReviewStep(step: string | null | undefined): string {
  if (!step) {
    return "—";
  }
  return REVIEW_STEP_LABELS[step] ?? step.replaceAll("_", " ");
}

export function PRReviewDetailView({ review }: PRReviewDetailProps) {
  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm text-slate-400">Pull Request</p>
            <h2 className="mt-1 text-xl font-semibold text-white">
              {review.owner}/{review.repository} #{review.pull_request_number}
            </h2>
            <p className="mt-2 text-slate-300">{review.pull_request_title || "Untitled PR"}</p>
          </div>
          <div className="text-right text-sm text-slate-400">
            <p>
              Status:{" "}
              <span className="text-slate-200 capitalize">{review.status}</span>
            </p>
            {review.current_step && review.status !== "completed" && (
              <p className="mt-1">
                Step:{" "}
                <span className="text-slate-200">{formatReviewStep(review.current_step)}</span>
              </p>
            )}
            <p className="mt-1">
              Risk:{" "}
              <span className="text-slate-200 capitalize">{review.overall_risk || "—"}</span>
            </p>
            <p className="mt-1">
              Findings: <span className="text-slate-200">{review.findings_count}</span>
            </p>
          </div>
        </div>

        {review.error && (
          <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {review.error}
          </div>
        )}

        {review.github_comment_url && (
          <p className="mt-4 text-sm">
            <a
              href={review.github_comment_url}
              target="_blank"
              rel="noreferrer"
              className="text-brand-200 hover:underline"
            >
              View GitHub comment
            </a>
          </p>
        )}
      </section>

      {review.mcp_enrichment && (
        <PrReviewMcpPanel enrichment={review.mcp_enrichment} />
      )}

      {review.review_markdown && (
        <section className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-6">
          <h3 className="text-lg font-semibold text-white">Review</h3>
          <pre className="mt-4 overflow-x-auto whitespace-pre-wrap text-sm text-slate-300">
            {review.review_markdown}
          </pre>
        </section>
      )}
    </div>
  );
}
