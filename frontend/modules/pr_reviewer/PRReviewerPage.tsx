"use client";

import { useState } from "react";
import axios from "axios";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth } from "@/components/auth/RequireAuth";
import {
  usePrReviewStatus,
  useStartPrReview,
} from "@/hooks/usePrReviewer";
import { PRReviewerSetupGuide } from "@/modules/pr_reviewer/PRReviewerSetupGuide";

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
    return "";
  }
  return REVIEW_STEP_LABELS[step] ?? step.replaceAll("_", " ");
}

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    return `Request failed with status ${error.response?.status ?? "unknown"}.`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "An unexpected error occurred.";
}

export function PRReviewerPage() {
  const [owner, setOwner] = useState("");
  const [repo, setRepo] = useState("");
  const [pullRequestNumber, setPullRequestNumber] = useState("");
  const [activeReviewId, setActiveReviewId] = useState<string | null>(null);
  const [userError, setUserError] = useState<string | null>(null);

  const startReview = useStartPrReview();
  const statusQuery = usePrReviewStatus(activeReviewId, Boolean(activeReviewId));

  const handleReview = async () => {
    setUserError(null);
    const prNumber = Number(pullRequestNumber);
    if (!owner.trim() || !repo.trim() || !Number.isInteger(prNumber) || prNumber < 1) {
      setUserError("Owner, repository, and a valid pull request number are required.");
      return;
    }

    try {
      const response = await startReview.mutateAsync({
        owner: owner.trim(),
        repo: repo.trim(),
        pull_request_number: prNumber,
      });
      setActiveReviewId(response.review_id);
    } catch (error) {
      setUserError(getErrorMessage(error));
    }
  };

  return (
    <RequireAuth>
      <AppShell>
        <div className="space-y-6">
          <section>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">PR Reviewer</h1>
            <p className="mt-2 text-slate-600">
              AI-powered DevOps review for GitHub Pull Requests
            </p>
          </section>

          <PRReviewerSetupGuide />

          <section className="panel p-6">
            <h2 className="panel-title text-lg">Manual Review</h2>
            <p className="mt-2 text-sm text-slate-600">
              Trigger a DevOps review without waiting for a webhook event.
            </p>

            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <label className="block text-sm">
                <span className="font-medium text-slate-800">Owner</span>
                <input
                  value={owner}
                  onChange={(event) => setOwner(event.target.value)}
                  placeholder="ideaweaver-ai"
                  className="input-field mt-1"
                />
              </label>
              <label className="block text-sm">
                <span className="font-medium text-slate-800">Repository</span>
                <input
                  value={repo}
                  onChange={(event) => setRepo(event.target.value)}
                  placeholder="devops-testing"
                  className="input-field mt-1"
                />
              </label>
              <label className="block text-sm">
                <span className="font-medium text-slate-800">Pull Request Number</span>
                <input
                  value={pullRequestNumber}
                  onChange={(event) => setPullRequestNumber(event.target.value)}
                  placeholder="1"
                  inputMode="numeric"
                  className="input-field mt-1"
                />
              </label>
            </div>

            {userError && (
              <div className="mt-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm font-medium text-red-800">
                {userError}
              </div>
            )}

            {activeReviewId && statusQuery.data && (
              <div className="mt-4 rounded-lg border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-900">
                Review <span className="font-mono">{activeReviewId}</span> is{" "}
                <span className="capitalize">{statusQuery.data.status}</span>
                {statusQuery.data.current_step
                  ? ` (${formatReviewStep(statusQuery.data.current_step)})`
                  : ""}.
                {" "}
                <Link
                  href={`/pr-reviewer/reviews/${activeReviewId}?from=${encodeURIComponent("/pr-reviewer")}`}
                  className="underline"
                >
                  View details
                </Link>
                {" · "}
                <Link href="/pr-reviewer/investigations" className="underline">
                  View investigations
                </Link>
              </div>
            )}

            <button
              type="button"
              onClick={handleReview}
              disabled={startReview.isPending}
              className="mt-5 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-400 disabled:opacity-60"
            >
              {startReview.isPending ? "Starting Review..." : "Review Pull Request"}
            </button>
          </section>
        </div>
      </AppShell>
    </RequireAuth>
  );
}

export default PRReviewerPage;
