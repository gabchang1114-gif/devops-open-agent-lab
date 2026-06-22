"use client";

import type { CloudCostAnalysis, CloudCostAnalysisFinding } from "@/types/cloudCost";
import { LlmProviderBadge } from "@/components/LlmProviderBadge";

function riskClass(risk: string) {
  switch (risk.toLowerCase()) {
    case "high":
      return "border-red-500/20 bg-red-500/10 text-red-300";
    case "medium":
      return "border-amber-500/20 bg-amber-500/10 text-amber-300";
    case "low":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";
    default:
      return "border-slate-500/20 bg-slate-500/10 text-slate-300";
  }
}

function severityClass(severity: string) {
  switch (severity.toLowerCase()) {
    case "high":
      return "border-red-500/20 bg-red-500/10 text-red-300";
    case "medium":
      return "border-amber-500/20 bg-amber-500/10 text-amber-300";
    default:
      return "border-slate-500/20 bg-slate-500/10 text-slate-300";
  }
}

function statusClass(status: string) {
  switch (status) {
    case "confirmed":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";
    case "potential":
      return "border-amber-500/20 bg-amber-500/10 text-amber-300";
    default:
      return "border-slate-500/20 bg-slate-500/10 text-slate-300";
  }
}

function formatSavings(amount: number, currency: string) {
  if (!amount || amount <= 0) {
    return "Qualitative only (no exact amount in this scan)";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency || "USD",
    maximumFractionDigits: 0,
  }).format(amount);
}

function FindingCard({ finding }: { finding: CloudCostAnalysisFinding }) {
  return (
    <div className="px-6 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h4 className="text-sm font-medium text-slate-100">{finding.title}</h4>
          <p className="mt-1 font-mono text-xs text-slate-500">{finding.resource_id}</p>
          <p className="mt-1 text-xs text-slate-400">
            {finding.resource_type} · {finding.status.replaceAll("_", " ")}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className={`status-pill border ${severityClass(finding.severity)}`}>
            {finding.severity}
          </span>
          <span className={`status-pill border ${statusClass(finding.status)}`}>
            {finding.status.replaceAll("_", " ")}
          </span>
          {finding.safe_to_delete ? (
            <span className="status-pill border border-red-500/20 bg-red-500/10 text-red-300">
              review delete
            </span>
          ) : (
            <span className="status-pill border border-slate-500/20 bg-slate-500/10 text-slate-300">
              validate first
            </span>
          )}
        </div>
      </div>
      <p className="mt-3 text-sm text-slate-300">{finding.reason}</p>
      <p className="mt-2 text-sm text-emerald-200/90">{finding.recommendation}</p>
      <p className="mt-2 text-xs text-slate-500">
        Est. savings: {formatSavings(finding.estimated_savings.amount, finding.estimated_savings.currency)}
        {finding.estimated_savings.amount > 0 ? "/month" : ""} · {finding.estimated_savings.confidence} confidence
      </p>
      {finding.estimated_savings.note && (
        <p className="mt-1 text-xs text-slate-500">{finding.estimated_savings.note}</p>
      )}
      {finding.validation_steps.length > 0 && (
        <div className="mt-3">
          <p className="section-label mb-2">Validation Steps</p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-400">
            {finding.validation_steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </div>
      )}
      {finding.aws_cli_commands.length > 0 && (
        <div className="mt-3">
          <p className="section-label mb-2">AWS CLI Commands</p>
          <div className="space-y-2">
            {finding.aws_cli_commands.map((command) => (
              <pre
                key={command}
                className="overflow-x-auto rounded-lg border border-white/[0.06] bg-slate-950/70 px-3 py-2 font-mono text-xs text-slate-300"
              >
                {command}
              </pre>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface CloudCostAnalysisReportProps {
  analysis: CloudCostAnalysis;
}

export function CloudCostAnalysisReport({ analysis }: CloudCostAnalysisReportProps) {
  const savings = analysis.estimated_monthly_savings;

  return (
    <div className="panel-accent overflow-hidden">
      <div className="border-b border-white/[0.06] px-6 py-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="panel-subtitle mb-1">AI Cost Analysis</p>
            <h2 className="panel-title">Optimization Report</h2>
          </div>
          <LlmProviderBadge provider={analysis.llm_provider} />
        </div>
        {analysis.llm_error && (
          <p className="mt-3 text-sm text-amber-300/90">
            Investigation completed, but AI analysis returned a partial result: {analysis.llm_error}
          </p>
        )}
      </div>

      <div className="grid gap-4 border-b border-white/[0.06] p-6 sm:grid-cols-3">
        <div className="rounded-xl border border-white/[0.06] bg-slate-950/40 px-4 py-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Summary</p>
          <p className="mt-2 text-sm leading-relaxed text-slate-200">{analysis.summary}</p>
        </div>
        <div className="rounded-xl border border-white/[0.06] bg-slate-950/40 px-4 py-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Overall Risk</p>
          <span className={`status-pill mt-2 inline-flex border ${riskClass(analysis.overall_risk)}`}>
            {analysis.overall_risk}
          </span>
        </div>
        <div className="rounded-xl border border-white/[0.06] bg-slate-950/40 px-4 py-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Estimated Monthly Savings</p>
          <p className="mt-2 text-lg font-semibold text-white">
            {formatSavings(savings.amount, savings.currency)}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Confidence: {savings.confidence}
            {savings.note ? ` · ${savings.note}` : ""}
          </p>
        </div>
      </div>

      <div className="border-b border-white/[0.06] px-6 py-4">
        <h3 className="section-label">Findings ({analysis.findings.length})</h3>
      </div>
      {analysis.findings.length === 0 ? (
        <p className="px-6 py-4 text-sm text-slate-400">No AI findings were returned for this scan.</p>
      ) : (
        <div className="divide-y divide-white/[0.04]">
          {analysis.findings.map((finding) => (
            <FindingCard key={`${finding.resource_id}-${finding.title}`} finding={finding} />
          ))}
        </div>
      )}

      {(analysis.data_gaps.length > 0 || analysis.next_steps.length > 0) && (
        <div className="grid gap-4 border-t border-white/[0.06] p-6 sm:grid-cols-2">
          {analysis.data_gaps.length > 0 && (
            <div>
              <p className="section-label mb-2">Data Gaps</p>
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-400">
                {analysis.data_gaps.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
          {analysis.next_steps.length > 0 && (
            <div>
              <p className="section-label mb-2">Next Steps</p>
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-400">
                {analysis.next_steps.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
