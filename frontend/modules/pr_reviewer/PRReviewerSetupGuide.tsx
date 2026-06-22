"use client";

import { getApiBaseUrl } from "@/services/api";

export function PRReviewerSetupGuide() {
  const webhookUrl = `${getApiBaseUrl()}/api/v1/pr-reviewer/webhook`;

  return (
    <section className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-6">
      <h2 className="text-lg font-semibold text-white">Setup Instructions</h2>
      <p className="mt-2 text-sm text-slate-400">
        Configure a GitHub webhook on your repository to trigger automatic DevOps PR reviews.
      </p>

      <dl className="mt-5 space-y-4 text-sm">
        <div>
          <dt className="font-medium text-slate-300">Webhook URL</dt>
          <dd className="mt-1 rounded-lg border border-white/[0.08] bg-slate-900/60 px-3 py-2 font-mono text-xs text-brand-200">
            {webhookUrl}
          </dd>
        </div>
        <div>
          <dt className="font-medium text-slate-300">Content type</dt>
          <dd className="mt-1 text-slate-400">application/json</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-300">Events</dt>
          <dd className="mt-1 text-slate-400">pull_request (opened, synchronize, reopened)</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-300">Secret</dt>
          <dd className="mt-1 text-slate-400">
            Set <code className="text-brand-200">GITHUB_WEBHOOK_SECRET</code> in backend{" "}
            <code className="text-brand-200">.env</code> and use the same value in GitHub.
          </dd>
        </div>
        <div>
          <dt className="font-medium text-slate-300">GitHub token</dt>
          <dd className="mt-1 text-slate-400">
            Set <code className="text-brand-200">GITHUB_TOKEN</code> with repo scope to fetch PR
            files and post review comments.
          </dd>
        </div>
      </dl>
    </section>
  );
}
