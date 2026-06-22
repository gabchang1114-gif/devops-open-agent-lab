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
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-950 px-4 py-10">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-grid-pattern bg-grid opacity-30"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-0 h-72 w-72 -translate-x-1/2 rounded-full bg-brand-600/10 blur-3xl"
      />

      <div className="panel-accent relative w-full max-w-md p-8 shadow-glow-sm">
        <div className="mb-8">
          <Link href="/" className="mb-4 inline-flex items-center gap-2 text-sm text-slate-400">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-brand-500/20 bg-brand-500/10 text-brand-300">
              D
            </span>
            DevOps Open Agent
          </Link>
          <h1 className="text-3xl font-bold tracking-tight text-white">{title}</h1>
          <p className="mt-2 text-sm leading-relaxed text-slate-400">{subtitle}</p>
        </div>

        {children}

        <div className="mt-6 text-center text-sm text-slate-400">{footer}</div>
      </div>
    </div>
  );
}
