"use client";

import { useState } from "react";
import type { JudgeVerdict } from "@/types/investigation";
import { LlmProviderBadge } from "@/components/LlmProviderBadge";

interface JudgeVerdictCardProps {
  verdict: JudgeVerdict | null | undefined;
}

function verdictConfig(verdict: string) {
  switch (verdict) {
    case "agree":
      return {
        label: "Agree",
        description: "The judge confirms the diagnosis is accurate and well-grounded.",
        border: "border-emerald-500/25",
        bg: "bg-emerald-500/10",
        text: "text-emerald-300",
        icon: "\u2713",
        defaultOpen: false,
      };
    case "disagree":
      return {
        label: "Disagree",
        description: "The judge found significant issues with the diagnosis.",
        border: "border-red-500/25",
        bg: "bg-red-500/10",
        text: "text-red-300",
        icon: "\u2717",
        defaultOpen: true,
      };
    default:
      return {
        label: "Partially Agree",
        description: "The judge found the diagnosis mostly correct but with gaps.",
        border: "border-amber-500/25",
        bg: "bg-amber-500/10",
        text: "text-amber-300",
        icon: "~",
        defaultOpen: true,
      };
  }
}

function confidenceStyles(score: number) {
  if (score >= 90) return { text: "text-emerald-400", ring: "stroke-emerald-400" };
  if (score >= 70) return { text: "text-brand-400", ring: "stroke-brand-400" };
  if (score >= 40) return { text: "text-amber-400", ring: "stroke-amber-400" };
  return { text: "text-red-400", ring: "stroke-red-400" };
}

function ConfidenceRing({ score }: { score: number }) {
  const styles = confidenceStyles(score);
  const radius = 22;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative flex h-[56px] w-[56px] items-center justify-center">
      <svg className="-rotate-90" width="56" height="56" viewBox="0 0 56 56" aria-hidden>
        <circle
          cx="28"
          cy="28"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="4"
        />
        <circle
          cx="28"
          cy="28"
          r={radius}
          fill="none"
          className={styles.ring}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute text-center">
        <div className={`text-sm font-bold tabular-nums leading-none ${styles.text}`}>
          {score}%
        </div>
      </div>
    </div>
  );
}

function IssueList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <section>
      <h4 className="section-label">{title}</h4>
      <ul className="space-y-2">
        {items.map((item, index) => (
          <li key={index} className="flex gap-3 text-sm leading-relaxed text-slate-300">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md border border-white/[0.08] bg-slate-800/80 text-[11px] font-medium text-slate-400">
              {index + 1}
            </span>
            <span className="pt-0.5">{item}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function JudgeVerdictCard({ verdict }: JudgeVerdictCardProps) {
  if (!verdict) return null;

  const config = verdictConfig(verdict.verdict);
  const [isOpen, setIsOpen] = useState(config.defaultOpen);

  const hasIssues =
    verdict.factual_issues.length > 0 ||
    verdict.missed_evidence.length > 0 ||
    verdict.command_safety_concerns.length > 0 ||
    verdict.suggested_improvements.length > 0;

  return (
    <div className="panel-accent animate-fade-in mt-6 overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between gap-4 px-6 py-4 text-left transition hover:bg-white/[0.02]"
      >
        <div className="flex items-center gap-3">
          <div
            className={`flex h-8 w-8 items-center justify-center rounded-lg border ${config.border} ${config.bg} text-sm font-bold ${config.text}`}
          >
            {config.icon}
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold text-white">
                AI Verification
              </span>
              <span
                className={`inline-flex rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${config.border} ${config.bg} ${config.text}`}
              >
                {config.label}
              </span>
              <LlmProviderBadge provider={verdict.llm_provider} />
            </div>
            <p className="mt-0.5 text-xs text-slate-500">{config.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <ConfidenceRing score={verdict.confidence_score} />
          <svg
            className={`h-4 w-4 text-slate-500 transition-transform ${isOpen ? "rotate-180" : ""}`}
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden
          >
            <path
              fillRule="evenodd"
              d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
              clipRule="evenodd"
            />
          </svg>
        </div>
      </button>

      {isOpen && (
        <div className="space-y-5 border-t border-white/[0.06] px-6 py-5">
          {verdict.llm_error && (
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
              {verdict.llm_error}
            </div>
          )}

          <section>
            <h4 className="section-label">Reasoning</h4>
            <p className="text-sm leading-relaxed text-slate-300">
              {verdict.reasoning}
            </p>
          </section>

          {hasIssues && (
            <div className="space-y-5">
              <IssueList title="Factual Issues" items={verdict.factual_issues} />
              <IssueList title="Missed Evidence" items={verdict.missed_evidence} />
              <IssueList
                title="Command Safety Concerns"
                items={verdict.command_safety_concerns}
              />
              <IssueList
                title="Suggested Improvements"
                items={verdict.suggested_improvements}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
