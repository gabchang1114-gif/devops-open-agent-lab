"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { usePrReviewDetail } from "@/hooks/usePrReviewer";
import { PRReviewDetailView } from "@/modules/pr_reviewer/PRReviewDetail";

export default function PrReviewDetailPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const reviewId = params.id;
  const backHref = searchParams.get("from") || "/pr-reviewer/investigations";
  const backLabel = backHref.includes("investigations")
    ? "Back to Investigations"
    : "Back to PR Reviewer";
  const reviewQuery = usePrReviewDetail(reviewId);

  return (
    <RequireAuth>
      <AppShell>
        <div className="space-y-6">
          <div>
            <Link href={backHref} className="text-sm text-brand-200 hover:underline">
              ← {backLabel}
            </Link>
            <h1 className="mt-3 text-2xl font-bold text-white">Review Detail</h1>
          </div>

          {reviewQuery.isLoading && (
            <p className="text-sm text-slate-400">Loading review...</p>
          )}

          {reviewQuery.error && (
            <p className="text-sm text-red-300">Unable to load review.</p>
          )}

          {reviewQuery.data && <PRReviewDetailView review={reviewQuery.data} />}
        </div>
      </AppShell>
    </RequireAuth>
  );
}
