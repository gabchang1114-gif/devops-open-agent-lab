"use client";

import { getApiBaseUrl } from "@/services/api";

export function PRReviewerSetupGuide() {
  const webhookUrl = `${getApiBaseUrl()}/api/v1/pr-reviewer/webhook`;

  return (
    <section className="panel p-6">
      <h2 className="panel-title text-lg">Setup Instructions</h2>
      <p className="mt-2 text-sm text-slate-600">
        Configure a GitHub webhook on your repository to trigger automatic DevOps PR reviews.
      </p>

      <dl className="mt-5 space-y-4 text-sm">
        <div>
          <dt className="font-semibold text-slate-800">Webhook URL</dt>
          <dd className="mt-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-xs font-medium text-brand-700">
            {webhookUrl}
          </dd>
        </div>
        <div>
          <dt className="font-semibold text-slate-800">Content type</dt>
          <dd className="mt-1 text-slate-700">application/json</dd>
        </div>
        <div>
          <dt className="font-semibold text-slate-800">Events</dt>
          <dd className="mt-1 text-slate-700">pull_request (opened, synchronize, reopened)</dd>
        </div>
        <div>
          <dt className="font-semibold text-slate-800">Secret</dt>
          <dd className="mt-1 text-slate-700">
            Set{" "}
            <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs font-semibold text-brand-700">
              GITHUB_WEBHOOK_SECRET
            </code>{" "}
            in backend{" "}
            <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs font-semibold text-brand-700">
              .env
            </code>{" "}
            and use the same value in GitHub.
          </dd>
        </div>
        <div>
          <dt className="font-semibold text-slate-800">GitHub token</dt>
          <dd className="mt-1 text-slate-700">
            Set{" "}
            <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs font-semibold text-brand-700">
              GITHUB_TOKEN
            </code>{" "}
            with repo scope to fetch PR files and post review comments.
          </dd>
        </div>
      </dl>
    </section>
  );
}
