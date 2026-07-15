import { apiClient } from "@/services/api";
import type {
  InvestigationHistoryResponse,
  InvestigationResultResponse,
  InvestigationStartResponse,
  InvestigationStatusResponse,
  StartInvestigationRequest,
} from "@/types/investigation";
import type { ClusterListResponse } from "@/types/system";
import type { SystemReadinessResponse } from "@/types/system";

export const investigationApi = {
  async startInvestigation(
    request: StartInvestigationRequest,
  ): Promise<InvestigationStartResponse> {
    const response = await apiClient.post<InvestigationStartResponse>(
      "/api/v1/investigate",
      {
        cluster_id: request.cluster_id,
        include_ai: request.include_ai ?? true,
        include_rag: request.include_rag ?? false,
        include_judge: request.include_judge ?? false,
        judge_provider: request.judge_provider ?? null,
        judge_model: request.judge_model ?? null,
        namespace: request.namespace,
        agent_type: request.agent_type ?? "kubernetes",
        account_id: request.account_id,
        region: request.region,
        cloudwatch_window: request.cloudwatch_window,
        issue_type: request.issue_type,
        query: request.query ?? null,
      },
      { timeout: request.agent_type === "aws" ? 180_000 : undefined },
    );
    return response.data;
  },

  async getInvestigationStatus(id: string): Promise<InvestigationStatusResponse> {
    const response = await apiClient.get<InvestigationStatusResponse>(
      `/api/v1/investigations/${id}`,
    );
    return response.data;
  },

  async getInvestigationResult(id: string): Promise<InvestigationResultResponse> {
    const response = await apiClient.get<InvestigationResultResponse>(
      `/api/v1/investigations/${id}/result`,
    );
    return response.data;
  },

  async listInvestigations(agentType?: string): Promise<InvestigationHistoryResponse> {
    const response = await apiClient.get<InvestigationHistoryResponse>(
      "/api/v1/investigations",
      {
        params: agentType ? { agent_type: agentType } : undefined,
      },
    );
    return response.data;
  },

  async listClusters(): Promise<ClusterListResponse> {
    const response = await apiClient.get<ClusterListResponse>("/api/v1/clusters");
    return response.data;
  },

  async getReadiness(): Promise<SystemReadinessResponse> {
    const response = await apiClient.get<SystemReadinessResponse>(
      "/api/v1/system/readiness",
    );
    return response.data;
  },
};
