"use client";

import Link from "next/link";
import type { ReactNode } from "react";

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}

export function AuthLayout({ title, subtitle, children, footer }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen">
      {/* Brand panel */}
      <div className="relative hidden w-[42%] flex-col justify-between overflow-hidden bg-sidebar-gradient p-10 lg:flex">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-grid-pattern-dark bg-grid opacity-25"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -right-20 top-1/4 h-64 w-64 rounded-full bg-brand-500/20 blur-3xl"
        />

        <div className="relative">
          <div className="mb-8 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-cyan-600 shadow-glow-sm">
              <svg viewBox="0 0 24 24" fill="none" className="h-6 w-6 text-white" aria-hidden>
                <path
                  d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <div>
              <p className="text-lg font-bold text-white">DevOps Open Agent</p>
              <p className="text-xs text-slate-400">Operations Hub</p>
            </div>
          </div>
          <h2 className="max-w-sm text-3xl font-bold leading-tight text-white">
            AI-powered troubleshooting for modern infrastructure
          </h2>
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-slate-400">
            Investigate Kubernetes clusters, AWS resources, cloud costs, and pull requests —
            with institutional memory via RAG.
          </p>
        </div>

        <div className="relative flex flex-wrap gap-2">
          {["Open Source", "Self-Hostable", "Multi-Agent"].map((badge) => (
            <span
              key={badge}
              className="rounded-full border border-slate-600/50 bg-slate-800/50 px-3 py-1 text-xs text-slate-300"
            >
              {badge}
            </span>
          ))}
        </div>
      </div>

      {/* Form panel */}
      <div className="flex flex-1 items-center justify-center bg-surface px-4 py-10">
        <div className="panel-accent w-full max-w-md p-8 shadow-panel">
          <div className="mb-8 lg:hidden">
            <Link href="/" className="mb-4 inline-flex items-center gap-2 text-sm text-slate-600">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500 text-sm font-bold text-white">
                D
              </span>
              DevOps Open Agent
            </Link>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">{subtitle}</p>

          <div className="mt-8">{children}</div>

          <div className="mt-6 text-center text-sm text-slate-500">{footer}</div>
        </div>
      </div>
    </div>
  );
}
