"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { InvestigationProgress } from "@/components/InvestigationProgress";
import { CloudCostDetectorForm } from "@/modules/cloud_cost_detector/CloudCostDetectorForm";
import { CloudCostInvestigationResults } from "@/modules/cloud_cost_detector/CloudCostInvestigationResults";
import {
  useCloudCostAccount,
  useCloudCostRegions,
} from "@/hooks/useCloudCost";
import { useInvestigation } from "@/hooks/useInvestigation";
import {
  useInvestigationResult,
  useInvestigationStatus,
} from "@/hooks/useInvestigationStatus";
import { CLOUD_COST_INVESTIGATION_STEPS } from "@/types/investigation";
import type { CloudCostInvestigationResponse } from "@/types/cloudCost";

const TERMINAL_STATUSES = new Set(["success", "partial_success", "completed", "failed"]);

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return "Unable to reach the backend API. Start the backend and try again.";
    }
    const detail = error.response.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    return `Request failed with status ${error.response.status}.`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "An unexpected error occurred.";
}

export function CloudCostDetectorPage() {
  const [region, setRegion] = useState("");
  const [activeInvestigationId, setActiveInvestigationId] = useState<string | null>(null);
  const [userError, setUserError] = useState<string | null>(null);

  const accountQuery = useCloudCostAccount(region || undefined, true);
  const regionsQuery = useCloudCostRegions(region || undefined, true);
  const { startInvestigation, isStarting, startError, reset } = useInvestigation();
  const statusQuery = useInvestigationStatus(activeInvestigationId);
  const status = statusQuery.data?.status;
  const isTerminal = Boolean(status && TERMINAL_STATUSES.has(status));
  const resultQuery = useInvestigationResult(activeInvestigationId, isTerminal);

  const accountId = accountQuery.data?.account_id ?? "";

  useEffect(() => {
    const regions = regionsQuery.data?.regions ?? [];
    if (regions.length > 0 && !region) {
      setRegion(regions[0]);
    }
  }, [regionsQuery.data, region]);

  useEffect(() => {
    if (startError) {
      setUserError(getErrorMessage(startError));
    }
  }, [startError]);

  useEffect(() => {
    if (statusQuery.data?.error && statusQuery.data.status === "failed") {
      setUserError(statusQuery.data.error);
    }
  }, [statusQuery.data?.error, statusQuery.data?.status]);

  const handleAnalyze = async () => {
    if (!accountId || !region) {
      setUserError("Account and region are required before analyzing resources.");
      return;
    }

    setUserError(null);
    reset();

    try {
      const response = await startInvestigation({
        agent_type: "cloud_cost",
        account_id: accountId,
        region,
        include_ai: true,
      });
      setActiveInvestigationId(response.investigation_id);
    } catch (error) {
      setUserError(getErrorMessage(error));
    }
  };

  const cloudCostResult = (resultQuery.data?.cloud_cost_result ??
    null) as CloudCostInvestigationResponse | null;

  const accountError = accountQuery.isError ? getErrorMessage(accountQuery.error) : null;
  const regionsError = regionsQuery.isError ? getErrorMessage(regionsQuery.error) : null;

  return (
    <AppShell>
      {userError && (
        <div className="alert-error mb-6 flex gap-3">
          <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-500/20 text-xs text-red-300">
            !
          </span>
          <div>{userError}</div>
        </div>
      )}

      <div className="space-y-6">
        <CloudCostDetectorForm
          accountId={accountId}
          accountName={accountQuery.data?.account_name}
          region={region}
          regions={regionsQuery.data?.regions ?? []}
          onRegionChange={setRegion}
          onAnalyze={handleAnalyze}
          isLoading={isStarting || status === "running"}
          accountLoading={accountQuery.isLoading}
          regionsLoading={regionsQuery.isLoading}
          accountError={accountError}
          regionsError={regionsError}
        />

        {activeInvestigationId && statusQuery.data && (
          <InvestigationProgress
            currentStep={statusQuery.data.current_step}
            progressPercentage={statusQuery.data.progress_percentage}
            status={statusQuery.data.status}
            steps={CLOUD_COST_INVESTIGATION_STEPS}
            title="Analyzing AWS Cost Optimization Opportunities..."
          />
        )}

        {resultQuery.isLoading && isTerminal && (
          <div className="alert-loading flex items-center gap-3">
            <span className="inline-flex h-4 w-4 animate-spin rounded-full border-2 border-emerald-500/30 border-t-emerald-400" />
            Loading analysis results...
          </div>
        )}

        {resultQuery.isError && (
          <div className="alert-error">
            Failed to load analysis result. {getErrorMessage(resultQuery.error)}
          </div>
        )}

        {isTerminal && cloudCostResult && (
          <CloudCostInvestigationResults data={cloudCostResult} />
        )}
      </div>
    </AppShell>
  );
}

export default function CloudCostDetectorRoute() {
  return (
    <RequireAuth>
      <CloudCostDetectorPage />
    </RequireAuth>
  );
}
