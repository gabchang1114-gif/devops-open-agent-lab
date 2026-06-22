"use client";

import { useQuery } from "@tanstack/react-query";
import { investigationApi } from "@/services/investigationApi";

const TERMINAL_STATUSES = new Set(["completed", "success", "partial_success", "failed"]);

export function useInvestigationStatus(investigationId: string | null) {
  return useQuery({
    queryKey: ["investigation", "status", investigationId],
    queryFn: () => investigationApi.getInvestigationStatus(investigationId!),
    enabled: Boolean(investigationId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status || TERMINAL_STATUSES.has(status)) {
        return false;
      }
      return 2000;
    },
  });
}

export function useInvestigationResult(investigationId: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ["investigation", "result", investigationId],
    queryFn: () => investigationApi.getInvestigationResult(investigationId!),
    enabled: Boolean(investigationId) && enabled,
  });
}

export function useInvestigationHistory(agentType?: string) {
  return useQuery({
    queryKey: ["investigations", "history", agentType ?? "all"],
    queryFn: () => investigationApi.listInvestigations(agentType),
    refetchInterval: 10000,
  });
}
