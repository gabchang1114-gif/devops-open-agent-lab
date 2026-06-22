"use client";

import { SystemStatus } from "@/components/SystemStatus";

export function HeroSection() {
  return (
    <section className="flex min-h-screen flex-col items-center justify-center px-6">
      <div className="w-full max-w-2xl rounded-2xl border border-slate-700/60 bg-slate-900/70 p-10 text-center shadow-2xl backdrop-blur-sm">
        <div className="mb-6 inline-flex items-center rounded-full border border-brand-500/30 bg-brand-500/10 px-4 py-1 text-sm text-brand-100">
          Open Source · Self-Hostable · Cloud Agnostic
        </div>

        <h1 className="mb-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
          Kubernetes Debugging Agent
        </h1>

        <p className="mb-10 text-lg text-slate-300 sm:text-xl">
          AI-Powered Kubernetes Troubleshooting Platform
        </p>

        <button
          type="button"
          disabled
          className="mb-8 inline-flex cursor-not-allowed items-center justify-center rounded-lg bg-brand-600 px-8 py-3 text-base font-semibold text-white opacity-80 transition hover:bg-brand-700 disabled:opacity-60"
          title="Investigation workflows coming in a future phase"
        >
          Investigate Cluster
        </button>

        <SystemStatus />
      </div>
    </section>
  );
}
