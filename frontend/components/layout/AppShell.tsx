"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { SystemStatus } from "@/components/SystemStatus";
import { getActiveAgent, PLATFORM, PLATFORM_AGENTS } from "@/lib/platform";

function isNavActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/";
  }
  return pathname.startsWith(href);
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const activeAgent = getActiveAgent(pathname);

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-grid-pattern bg-grid opacity-40"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -left-32 top-0 h-[28rem] w-[28rem] rounded-full bg-brand-600/10 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -right-24 top-1/3 h-[24rem] w-[24rem] rounded-full bg-indigo-600/8 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-0 left-1/2 h-[20rem] w-[36rem] -translate-x-1/2 rounded-full bg-brand-900/20 blur-3xl"
      />

      <div className="relative mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        <header className="mb-8 animate-fade-in">
          <div className="mb-5 flex flex-wrap items-center gap-3">
            {PLATFORM.badges.map((badge) => (
              <div
                key={badge}
                className={`inline-flex items-center rounded-full border px-3.5 py-1.5 text-xs font-medium tracking-wide ${
                  badge === "Open Source"
                    ? "gap-2 border-brand-500/20 bg-brand-500/10 text-brand-200"
                    : "border-white/[0.08] bg-white/[0.03] text-slate-400"
                }`}
              >
                {badge === "Open Source" && (
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-400 shadow-[0_0_8px_rgba(96,165,250,0.8)]" />
                )}
                {badge}
              </div>
            ))}
          </div>

          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <div className="mb-3 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-brand-500/25 bg-gradient-to-br from-brand-500/20 to-brand-700/10 shadow-glow-sm">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    className="h-6 w-6 text-brand-300"
                    aria-hidden
                  >
                    <path
                      d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
              </div>
              <h1 className="mb-2 bg-gradient-to-br from-white via-slate-100 to-slate-400 bg-clip-text text-4xl font-bold tracking-tight text-transparent sm:text-5xl">
                {PLATFORM.name}
              </h1>
              <p className="text-base leading-relaxed text-slate-400 sm:text-lg">
                {PLATFORM.tagline}
              </p>
              <p className="mt-3 text-sm font-medium text-slate-300">{activeAgent.name}</p>
            </div>

            <div className="flex shrink-0 flex-col gap-3 lg:items-end">
              <div className="panel-accent px-5 py-4 lg:min-w-[280px]">
                <SystemStatus />
              </div>
              {user && (
                <div className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-slate-900/55 px-4 py-2.5">
                  <span className="text-sm text-slate-300">{user.email}</span>
                  <button
                    type="button"
                    onClick={logout}
                    className="rounded-lg border border-white/[0.08] px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:border-red-500/30 hover:bg-red-500/10 hover:text-red-200"
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>

          <nav className="mt-8 flex flex-wrap gap-2 border-b border-white/[0.06]">
            {PLATFORM_AGENTS.map((agent) => {
              const active = activeAgent.id === agent.id;
              return (
                <Link
                  key={agent.id}
                  href={agent.href}
                  className={`relative px-4 py-3 text-sm font-medium transition ${
                    active ? "text-white" : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {agent.name}
                  {!agent.available && (
                    <span className="ml-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-200">
                      Soon
                    </span>
                  )}
                  {active && (
                    <span className="absolute inset-x-0 -bottom-px h-0.5 rounded-full bg-brand-500" />
                  )}
                </Link>
              );
            })}
          </nav>

          {activeAgent.nav.length > 0 && (
            <nav className="mt-3 flex gap-2 border-b border-white/[0.04]">
              {activeAgent.nav.map((item) => {
                const active = isNavActive(pathname, item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`relative px-3 py-2.5 text-sm transition ${
                      active
                        ? "font-medium text-brand-300"
                        : "text-slate-500 hover:text-slate-300"
                    }`}
                  >
                    {item.label}
                    {active && (
                      <span className="absolute inset-x-0 -bottom-px h-0.5 rounded-full bg-brand-400/70" />
                    )}
                  </Link>
                );
              })}
            </nav>
          )}
        </header>

        {children}
      </div>
    </div>
  );
}
