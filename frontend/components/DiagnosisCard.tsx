"use client";

import type {
  DiagnosisEvidence,
  DiagnosisResult,
  InvestigationPayload,
  PodIssueDiagnosis,
} from "@/types/investigation";
import { LlmProviderBadge } from "@/components/LlmProviderBadge";
import { JudgeVerdictCard } from "@/components/JudgeVerdictCard";

interface DiagnosisCardProps {
  diagnosis: DiagnosisResult | null | undefined;
  result?: InvestigationPayload | null;
  status?: string;
  errorMessage?: string | null;
  commandLabel?: string;
}

function isClusterHealthy(result?: InvestigationPayload | null): boolean {
  if (!result?.investigation) {
    return false;
  }
  const investigation = result.investigation as {
    pods?: { healthy?: boolean; problematic_pods?: unknown[] };
    deployments?: { healthy?: boolean; issues?: unknown[] };
    network?: { healthy?: boolean; issues?: unknown[] };
  };
  return (
    Boolean(investigation.pods?.healthy) &&
    (investigation.pods?.problematic_pods?.length ?? 0) === 0 &&
    Boolean(investigation.deployments?.healthy) &&
    (investigation.deployments?.issues?.length ?? 0) === 0 &&
    Boolean(investigation.network?.healthy) &&
    (investigation.network?.issues?.length ?? 0) === 0
  );
}

function reasonBadgeClass(reason: string): string {
  const lowered = reason.toLowerCase();
  if (lowered.includes("imagepull") || lowered.includes("errimage")) {
    return "border-amber-500/25 bg-amber-500/10 text-amber-200";
  }
  if (lowered.includes("crash") || lowered.includes("error")) {
    return "border-red-500/25 bg-red-500/10 text-red-200";
  }
  if (lowered.includes("oom")) {
    return "border-orange-500/25 bg-orange-500/10 text-orange-200";
  }
  return "border-brand-500/25 bg-brand-500/10 text-brand-200";
}

function confidenceStyles(score: number) {
  if (score >= 90) {
    return { text: "text-emerald-400", ring: "stroke-emerald-400" };
  }
  if (score >= 70) {
    return { text: "text-brand-400", ring: "stroke-brand-400" };
  }
  if (score >= 40) {
    return { text: "text-amber-400", ring: "stroke-amber-400" };
  }
  return { text: "text-red-400", ring: "stroke-red-400" };
}

function ConfidenceRing({ score }: { score: number }) {
  const styles = confidenceStyles(score);
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative flex h-[72px] w-[72px] items-center justify-center">
      <svg className="-rotate-90" width="72" height="72" viewBox="0 0 72 72" aria-hidden>
        <circle
          cx="36"
          cy="36"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="5"
        />
        <circle
          cx="36"
          cy="36"
          r={radius}
          fill="none"
          className={styles.ring}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute text-center">
        <div className={`text-lg font-bold tabular-nums leading-none ${styles.text}`}>
          {score}%
        </div>
      </div>
    </div>
  );
}

function EvidenceList({ evidence }: { evidence: DiagnosisEvidence[] }) {
  if (evidence.length === 0) {
    return <p className="text-sm text-slate-500">No evidence items were returned.</p>;
  }

  return (
    <ul className="space-y-2">
      {evidence.map((item, index) => (
        <li
          key={`${item.source}-${index}`}
          className="rounded-xl border border-white/[0.05] bg-slate-950/50 px-4 py-3"
        >
          <span className="inline-flex rounded-md border border-brand-500/20 bg-brand-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-brand-300">
            {item.source}
          </span>
          <p className="mt-2 text-sm leading-relaxed text-slate-300">{item.detail}</p>
        </li>
      ))}
    </ul>
  );
}

function IssueSolutionCard({
  issue,
  index,
  total,
  commandLabel,
}: {
  issue: PodIssueDiagnosis;
  index: number;
  total: number;
  commandLabel: string;
}) {
  return (
    <article className="panel-accent overflow-hidden">
      <header className="border-b border-white/[0.06] bg-slate-950/40 px-6 py-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="panel-subtitle mb-1">
              Issue {index} of {total}
            </p>
            <h3 className="text-lg font-semibold tracking-tight text-white">{issue.pod}</h3>
            <p className="mt-1 font-mono text-xs text-slate-500">
              {issue.namespace} · {issue.status}
            </p>
          </div>
          <span
            className={`status-pill border ${reasonBadgeClass(issue.reason)}`}
          >
            {issue.reason}
          </span>
        </div>
      </header>

      <div className="space-y-5 p-6">
        <section className="rounded-xl border border-white/[0.05] bg-slate-950/40 p-4">
          <h4 className="section-label">Root Cause</h4>
          <p className="text-[15px] font-medium leading-relaxed text-white">{issue.root_cause}</p>
        </section>

        <section>
          <h4 className="section-label">Summary</h4>
          <p className="text-sm leading-relaxed text-slate-300">{issue.summary}</p>
        </section>

        <section>
          <h4 className="section-label">Evidence</h4>
          <EvidenceList evidence={issue.evidence} />
        </section>

        <section className="rounded-xl border border-brand-500/15 bg-gradient-to-br from-brand-500/10 to-transparent p-4">
          <h4 className="section-label">Suggested Fix</h4>
          <p className="whitespace-pre-line text-sm leading-relaxed text-slate-200">{issue.suggested_fix}</p>
        </section>

        {issue.kubectl_commands.length > 0 && (
          <section>
            <h4 className="section-label">{commandLabel}</h4>
            <div className="space-y-2">
              {issue.kubectl_commands.map((command, commandIndex) => (
                <pre key={commandIndex} className="code-block">
                  {command}
                </pre>
              ))}
            </div>
          </section>
        )}

        {issue.validation_steps.length > 0 && (
          <section>
            <h4 className="section-label">Validation Steps</h4>
            <ul className="space-y-2">
              {issue.validation_steps.map((step, stepIndex) => (
                <li key={stepIndex} className="flex gap-3 text-sm leading-relaxed text-slate-300">
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md border border-white/[0.08] bg-slate-800/80 text-[11px] font-medium text-slate-400">
                    {stepIndex + 1}
                  </span>
                  <span className="pt-0.5">{step}</span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </article>
  );
}

function SingleDiagnosisView({
  diagnosis,
  status,
  errorMessage,
  commandLabel,
}: {
  diagnosis: DiagnosisResult;
  status?: string;
  errorMessage?: string | null;
  commandLabel: string;
}) {
  return (
    <div className="panel-accent animate-fade-in p-6">
      <div className="mb-6 flex items-start justify-between gap-4 border-b border-white/[0.06] pb-5">
        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <p className="panel-subtitle mb-0">AI Analysis</p>
            <LlmProviderBadge provider={diagnosis.llm_provider} />
          </div>
          <h2 className="panel-title">Diagnosis</h2>
          {status === "partial_success" && (
            <p className="mt-2 rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
              Investigation completed, but AI reasoning returned a partial result.
            </p>
          )}
        </div>
        <div className="flex flex-col items-center gap-1">
          <ConfidenceRing score={diagnosis.confidence_score} />
          <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
            Confidence
          </div>
        </div>
      </div>

      {errorMessage && (
        <div className="mb-5 whitespace-pre-line rounded-xl border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          {errorMessage}
        </div>
      )}

      <section className="mb-5 rounded-xl border border-white/[0.05] bg-slate-950/40 p-4">
        <h3 className="section-label">Root Cause</h3>
        <p className="whitespace-pre-line text-[15px] font-medium leading-relaxed text-white">
          {diagnosis.root_cause}
        </p>
      </section>

      <section className="mb-5">
        <h3 className="section-label">Summary</h3>
        <p className="text-sm leading-relaxed text-slate-300">{diagnosis.summary}</p>
      </section>

      <section className="mb-5">
        <h3 className="section-label">Evidence</h3>
        <EvidenceList evidence={diagnosis.evidence} />
      </section>

      <section className="mb-5 rounded-xl border border-brand-500/15 bg-gradient-to-br from-brand-500/10 to-transparent p-4">
        <h3 className="section-label">Suggested Fix</h3>
        <p className="whitespace-pre-line text-sm leading-relaxed text-slate-200">{diagnosis.suggested_fix}</p>
      </section>

      {diagnosis.kubectl_commands.length > 0 && (
        <section className="mb-5">
          <h3 className="section-label">{commandLabel}</h3>
          <div className="space-y-2">
            {diagnosis.kubectl_commands.map((command, index) => (
              <pre key={index} className="code-block">
                {command}
              </pre>
            ))}
          </div>
          <p className="mt-2.5 text-xs leading-relaxed text-slate-500">
            Recommendations only. Review and run manually — no commands are executed automatically.
          </p>
        </section>
      )}

      {diagnosis.validation_steps.length > 0 && (
        <section className="mb-5">
          <h3 className="section-label">Validation Steps</h3>
          <ul className="space-y-2">
            {diagnosis.validation_steps.map((step, index) => (
              <li key={index} className="flex gap-3 text-sm leading-relaxed text-slate-300">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md border border-white/[0.08] bg-slate-800/80 text-[11px] font-medium text-slate-400">
                  {index + 1}
                </span>
                <span className="pt-0.5">{step}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {diagnosis.prevention_recommendation && (
        <section className="mb-5 rounded-xl border border-white/[0.05] bg-slate-950/40 p-4">
          <h3 className="section-label">Prevention Recommendation</h3>
          <p className="text-sm leading-relaxed text-slate-300">
            {diagnosis.prevention_recommendation}
          </p>
        </section>
      )}

      <section className="rounded-xl border border-dashed border-white/[0.08] bg-slate-950/30 px-4 py-3">
        <h3 className="section-label">Confidence Reason</h3>
        <p className="text-sm leading-relaxed text-slate-400">{diagnosis.confidence_reason}</p>
      </section>
    </div>
  );
}

function MultiIssueDiagnosisView({
  diagnosis,
  status,
  errorMessage,
  commandLabel,
}: {
  diagnosis: DiagnosisResult;
  status?: string;
  errorMessage?: string | null;
  commandLabel: string;
}) {
  const issues = diagnosis.issue_diagnoses ?? [];

  return (
    <div className="animate-fade-in space-y-6">
      <div className="panel-accent p-6">
        <div className="mb-5 flex items-start justify-between gap-4 border-b border-white/[0.06] pb-5">
          <div>
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <p className="panel-subtitle mb-0">AI Analysis</p>
              <LlmProviderBadge provider={diagnosis.llm_provider} />
            </div>
            <h2 className="panel-title">Investigation Overview</h2>
            {status === "partial_success" && (
              <p className="mt-2 rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
                Investigation completed, but AI reasoning returned a partial result.
              </p>
            )}
          </div>
          <div className="flex flex-col items-center gap-1">
            <ConfidenceRing score={diagnosis.confidence_score} />
            <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
              Confidence
            </div>
          </div>
        </div>

        {errorMessage && (
          <div className="mb-5 whitespace-pre-line rounded-xl border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
            {errorMessage}
          </div>
        )}

        <section className="mb-5">
          <h3 className="section-label">Overview</h3>
          <p className="text-sm leading-relaxed text-slate-300">{diagnosis.root_cause}</p>
        </section>

        <section className="mb-5 whitespace-pre-line rounded-xl border border-white/[0.05] bg-slate-950/40 p-4">
          <h3 className="section-label">Affected Issues</h3>
          <p className="text-sm leading-relaxed text-slate-300">{diagnosis.summary}</p>
        </section>

        <section className="rounded-xl border border-dashed border-white/[0.08] bg-slate-950/30 px-4 py-3">
          <h3 className="section-label">Confidence Reason</h3>
          <p className="text-sm leading-relaxed text-slate-400">{diagnosis.confidence_reason}</p>
        </section>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between gap-4 px-1">
          <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-400">
            Separate Solutions
          </h3>
          <span className="rounded-full border border-white/[0.08] bg-slate-800/60 px-3 py-1 text-xs font-medium text-slate-400">
            {issues.length} issues
          </span>
        </div>

        {issues.map((issue, index) => (
          <IssueSolutionCard
            key={issue.pod}
            issue={issue}
            index={index + 1}
            total={issues.length}
            commandLabel={commandLabel}
          />
        ))}
      </div>
    </div>
  );
}

export function DiagnosisCard({
  diagnosis,
  result,
  status,
  errorMessage,
  commandLabel = "kubectl Commands",
}: DiagnosisCardProps) {
  if (status === "failed") {
    return (
      <div className="panel-accent animate-fade-in border-red-500/20 bg-gradient-to-br from-red-500/10 to-red-950/20 p-6">
        <div className="mb-3 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-red-500/25 bg-red-500/15 text-red-300">
            ✕
          </div>
          <h2 className="panel-title text-red-100">Investigation Failed</h2>
        </div>
        <p className="whitespace-pre-line text-sm leading-relaxed text-red-100/90">
          {errorMessage || "The investigation could not be completed."}
        </p>
      </div>
    );
  }

  if (!diagnosis && isClusterHealthy(result)) {
    return (
      <div className="panel-accent animate-fade-in border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 to-emerald-950/20 p-6">
        <div className="mb-3 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-500/25 bg-emerald-500/15 text-emerald-300">
            ✓
          </div>
          <h2 className="panel-title text-emerald-100">Cluster Appears Healthy</h2>
        </div>
        <p className="whitespace-pre-line text-sm leading-relaxed text-emerald-100/90">
          No unhealthy resources detected.{"\n\n"}The selected cluster appears healthy based on the
          collected investigation evidence.
        </p>
      </div>
    );
  }

  if (!diagnosis) {
    if (status === "success" || status === "completed" || status === "partial_success") {
      return (
        <div className="panel-accent animate-fade-in p-6 text-sm leading-relaxed text-slate-300">
          Investigation completed without AI diagnosis. Enable AI reasoning to view RCA.
        </div>
      );
    }
    return null;
  }

  if ((diagnosis.issue_diagnoses?.length ?? 0) > 1) {
    return (
      <>
        <MultiIssueDiagnosisView
          diagnosis={diagnosis}
          status={status}
          errorMessage={errorMessage}
          commandLabel={commandLabel}
        />
        <JudgeVerdictCard verdict={diagnosis.judge_verdict} />
      </>
    );
  }

  return (
    <>
      <SingleDiagnosisView
        diagnosis={diagnosis}
        status={status}
        errorMessage={errorMessage}
        commandLabel={commandLabel}
      />
      <JudgeVerdictCard verdict={diagnosis.judge_verdict} />
    </>
  );
}
