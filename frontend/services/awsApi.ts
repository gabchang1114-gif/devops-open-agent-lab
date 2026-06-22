import { apiClient } from "@/services/api";
import type {
  AwsAccountsResponse,
  AwsInvestigationRequest,
  AwsInvestigationResponse,
  AwsRegionsResponse,
  AwsTopologyResult,
} from "@/types/aws";

export const awsApi = {
  async listAccounts(region?: string): Promise<AwsAccountsResponse> {
    const response = await apiClient.get<AwsAccountsResponse>("/api/v1/aws/accounts", {
      params: region ? { region } : undefined,
    });
    return response.data;
  },

  async listRegions(accountId: string, region?: string): Promise<AwsRegionsResponse> {
    const response = await apiClient.get<AwsRegionsResponse>("/api/v1/aws/regions", {
      params: {
        account_id: accountId,
        ...(region ? { region } : {}),
      },
    });
    return response.data;
  },

  async investigate(request: AwsInvestigationRequest): Promise<AwsInvestigationResponse> {
    const response = await apiClient.post<AwsInvestigationResponse>(
      "/api/v1/aws/investigate",
      {
        account_id: request.account_id,
        region: request.region,
        cloudwatch_window: request.cloudwatch_window ?? "24h",
        issue_type: request.issue_type ?? "full_scan",
        query: request.query ?? null,
        include_ai: request.include_ai ?? true,
      },
      { timeout: 180_000 },
    );
    return response.data;
  },

  async getTopology(accountId: string, region: string): Promise<AwsTopologyResult> {
    const response = await apiClient.get<AwsTopologyResult>("/api/v1/aws/topology", {
      params: {
        account_id: accountId,
        region,
      },
      timeout: 120_000,
    });
    return response.data;
  },
};
