"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { AppShell } from "@/components/layout/AppShell";
import { DiagnosisCard } from "@/components/DiagnosisCard";
import { InvestigationForm } from "@/components/InvestigationForm";
import { InvestigationProgress } from "@/components/InvestigationProgress";
import { useClusters, resolveDefaultCluster } from "@/hooks/useClusters";
import { useInvestigation } from "@/hooks/useInvestigation";
import {
  useInvestigationResult,
  useInvestigationStatus,
} from "@/hooks/useInvestigationStatus";

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

export function Dashboard() {
  const [clusterId, setClusterId] = useState("");
  const [activeInvestigationId, setActiveInvestigationId] = useState<string | null>(null);
  const [userError, setUserError] = useState<string | null>(null);

  const clustersQuery = useClusters();
  const { startInvestigation, isStarting, startError, reset } = useInvestigation();
  const statusQuery = useInvestigationStatus(activeInvestigationId);
  const status = statusQuery.data?.status;
  const isTerminal = Boolean(status && TERMINAL_STATUSES.has(status));
  const resultQuery = useInvestigationResult(activeInvestigationId, isTerminal);

  useEffect(() => {
    if (clustersQuery.data?.clusters?.length && !clusterId) {
      setClusterId(resolveDefaultCluster(clustersQuery.data.clusters));
    }
  }, [clustersQuery.data, clusterId]);

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

  const handleInvestigate = async () => {
    if (!clusterId) {
      setUserError("Select a cluster before starting an investigation.");
      return;
    }

    setUserError(null);
    reset();

    try {
      const response = await startInvestigation({
        cluster_id: clusterId,
        include_ai: true,
      });
      setActiveInvestigationId(response.investigation_id);
    } catch (error) {
      setUserError(getErrorMessage(error));
    }
  };

  const diagnosis =
    resultQuery.data?.diagnosis ?? resultQuery.data?.result?.diagnosis ?? null;
  const resultStatus = resultQuery.data?.status ?? status;
  const investigationResult = resultQuery.data?.result ?? null;

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
        <InvestigationForm
          clusters={clustersQuery.data?.clusters ?? []}
          clusterId={clusterId}
          onClusterChange={setClusterId}
          onInvestigate={handleInvestigate}
          isLoading={isStarting || status === "running"}
          disabled={status === "running"}
          clustersLoading={clustersQuery.isLoading}
          clustersError={clustersQuery.data?.error ?? null}
        />

        {activeInvestigationId && statusQuery.data && (
          <InvestigationProgress
            currentStep={statusQuery.data.current_step}
            progressPercentage={statusQuery.data.progress_percentage}
            status={statusQuery.data.status}
          />
        )}

        {resultQuery.isLoading && isTerminal && (
          <div className="alert-loading flex items-center gap-3">
            <span className="inline-flex h-4 w-4 animate-spin rounded-full border-2 border-brand-500/30 border-t-brand-400" />
            Loading diagnosis...
          </div>
        )}

        {resultQuery.isError && (
          <div className="alert-error">
            Failed to load investigation result. {getErrorMessage(resultQuery.error)}
          </div>
        )}

        {isTerminal && (
          <DiagnosisCard
            diagnosis={diagnosis}
            result={investigationResult}
            status={resultStatus}
            errorMessage={resultQuery.data?.error ?? diagnosis?.llm_error}
          />
        )}
      </div>
    </AppShell>
  );
}
