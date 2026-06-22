"use client";

import type {
  CloudCostAnalyzeResponse,
  CloudCostFinding,
  CloudCostFindingsSummary,
  CloudCostInvestigationResponse,
} from "@/types/cloudCost";
import { CloudCostAnalysisReport } from "@/modules/cloud_cost_detector/CloudCostAnalysisReport";
import { CloudCostDetectorResults } from "@/modules/cloud_cost_detector/CloudCostDetectorResults";

function formatSavings(amount: number, currency: string) {
  if (!amount || amount <= 0) {
    return "—";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency || "USD",
    maximumFractionDigits: 2,
  }).format(amount);
}

function severityClass(severity: string) {
  switch (severity) {
    case "high":
      return "border-red-500/20 bg-red-500/10 text-red-300";
    case "medium":
      return "border-amber-500/20 bg-amber-500/10 text-amber-300";
    default:
      return "border-slate-500/20 bg-slate-500/10 text-slate-300";
  }
}

function HeuristicFindingsPanel({ findings }: { findings: CloudCostFindingsSummary }) {
  if (findings.total_findings === 0) {
    return (
      <div className="panel-accent p-6">
        <h3 className="panel-title">Rule-Based Findings</h3>
        <p className="mt-2 text-sm text-slate-400">
          No unused or underutilized resources detected with current heuristics.
        </p>
      </div>
    );
  }

  return (
    <div className="panel-accent overflow-hidden">
      <div className="border-b border-white/[0.06] px-6 py-4">
        <p className="panel-subtitle mb-1">Pre-LLM Heuristics</p>
        <h2 className="panel-title">
          {findings.total_findings} rule-based signals · {findings.unused_count} unused ·{" "}
          {findings.underutilized_count} underutilized
        </h2>
      </div>
      <div className="divide-y divide-white/[0.04]">
        {findings.findings.map((finding: CloudCostFinding) => (
          <div key={finding.finding_id} className="px-6 py-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-mono text-xs text-slate-400">{finding.resource_id}</p>
                <p className="mt-1 text-sm text-slate-200">
                  {finding.resource_name ? `${finding.resource_name} · ` : ""}
                  {finding.resource_type} · {finding.category}
                </p>
              </div>
              <span className={`status-pill border ${severityClass(finding.severity)}`}>
                {finding.severity}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-300">{finding.reason}</p>
            {finding.monthly_savings_usd != null && finding.monthly_savings_usd > 0 && (
              <p className="mt-2 text-sm font-medium text-emerald-300">
                Est. savings:{" "}
                {new Intl.NumberFormat("en-US", {
                  style: "currency",
                  currency: "USD",
                  maximumFractionDigits: 2,
                }).format(finding.monthly_savings_usd)}
                /month
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function SavingsSummaryPanel({
  savings,
}: {
  savings: import("@/types/cloudCost").CloudCostSavingsSummary;
}) {
  const topServices = Object.entries(savings.regional_spend?.by_service ?? {}).slice(0, 5);

  return (
    <div className="panel-accent overflow-hidden">
      <div className="border-b border-white/[0.06] px-6 py-4">
        <p className="panel-subtitle mb-1">Cost Estimation</p>
        <h2 className="panel-title">
          {formatSavings(savings.total_monthly_savings_usd, savings.currency)} potential monthly savings
        </h2>
        <p className="mt-1 text-xs text-slate-500">{savings.note}</p>
      </div>
      <div className="grid gap-4 p-6 sm:grid-cols-2">
        <div>
          <p className="section-label mb-2">Per-Resource Estimates</p>
          <ul className="space-y-2 text-sm text-slate-300">
            {savings.resource_estimates.map((item) => (
              <li key={item.resource_id} className="rounded-lg border border-white/[0.06] px-3 py-2">
                <p className="font-mono text-xs text-slate-500">{item.resource_id}</p>
                <p>
                  {formatSavings(item.monthly_savings_usd, savings.currency)}/mo · {item.confidence}{" "}
                  confidence
                </p>
                <p className="mt-1 text-xs text-slate-500">{item.note}</p>
              </li>
            ))}
          </ul>
        </div>
        {savings.regional_spend && (
          <div>
            <p className="section-label mb-2">Regional Spend (Cost Explorer)</p>
            {savings.regional_spend.available ? (
              <>
                <p className="text-lg font-semibold text-white">
                  {formatSavings(savings.regional_spend.total_usd, savings.currency)}
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  {savings.regional_spend.period_start} → {savings.regional_spend.period_end}
                </p>
                {topServices.length > 0 && (
                  <ul className="mt-3 space-y-1 text-sm text-slate-400">
                    {topServices.map(([service, amount]) => (
                      <li key={service} className="flex justify-between gap-3">
                        <span className="truncate">{service}</span>
                        <span className="tabular-nums">{formatSavings(amount, savings.currency)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            ) : (
              <p className="text-sm text-slate-400">{savings.regional_spend.note}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

interface CloudCostInvestigationResultsProps {
  data: CloudCostInvestigationResponse;
}

export function CloudCostInvestigationResults({ data }: CloudCostInvestigationResultsProps) {
  const inventoryData: CloudCostAnalyzeResponse = {
    status: data.status,
    account: {
      account_id: data.account_id,
      account_name: data.account_name,
    },
    region: data.region,
    collected_at: data.collected_at,
    resources: data.resources,
    summary: data.summary,
    notes: data.notes,
    analysis: data.analysis,
    cost_savings: data.cost_savings,
  };

  return (
    <div className="space-y-6">
      {data.cost_savings && data.cost_savings.total_monthly_savings_usd > 0 && (
        <SavingsSummaryPanel savings={data.cost_savings} />
      )}
      {data.analysis && <CloudCostAnalysisReport analysis={data.analysis} />}
      <HeuristicFindingsPanel findings={data.findings} />
      <CloudCostDetectorResults data={inventoryData} />
    </div>
  );
}
