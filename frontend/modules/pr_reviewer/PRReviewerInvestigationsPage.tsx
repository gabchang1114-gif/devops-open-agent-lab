"use client";

import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { usePrReviewHistory } from "@/hooks/usePrReviewer";
import { PRReviewHistory } from "@/modules/pr_reviewer/PRReviewHistory";

export function PRReviewerInvestigationsPage() {
  const historyQuery = usePrReviewHistory(true, 100);

  return (
    <RequireAuth>
      <AppShell>
        <div className="space-y-6">
          <section>
            <h1 className="text-3xl font-bold tracking-tight text-white">Investigations</h1>
            <p className="mt-2 text-slate-400">
              Past GitHub PR DevOps reviews run by the PR Reviewer agent.
            </p>
          </section>

          <PRReviewHistory
            reviews={historyQuery.data?.reviews ?? []}
            isLoading={historyQuery.isLoading}
            title="PR Review History"
            subtitle="History"
            emptyStateHref="/pr-reviewer"
            emptyStateLabel="Run your first PR review"
          />
        </div>
      </AppShell>
    </RequireAuth>
  );
}

export default PRReviewerInvestigationsPage;
