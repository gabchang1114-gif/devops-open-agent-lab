import { apiClient } from "@/services/api";
import type {
  CloudCostAccount,
  CloudCostAnalyzeRequest,
  CloudCostAnalyzeResponse,
  CloudCostRegionsResponse,
} from "@/types/cloudCost";

export const cloudCostApi = {
  async getAccount(region?: string): Promise<CloudCostAccount> {
    const response = await apiClient.get<CloudCostAccount>(
      "/api/v1/cloud-cost-detector/accounts",
      { params: region ? { region } : undefined },
    );
    return response.data;
  },

  async listRegions(region?: string): Promise<CloudCostRegionsResponse> {
    const response = await apiClient.get<CloudCostRegionsResponse>(
      "/api/v1/cloud-cost-detector/regions",
      { params: region ? { region } : undefined },
    );
    return response.data;
  },

  async analyze(request: CloudCostAnalyzeRequest): Promise<CloudCostAnalyzeResponse> {
    const response = await apiClient.post<CloudCostAnalyzeResponse>(
      "/api/v1/cloud-cost-detector/analyze",
      { ...request, include_ai: request.include_ai ?? true },
      { timeout: 180_000 },
    );
    return response.data;
  },

  async analyzeInventory(
    request: import("@/types/cloudCost").CloudCostAnalyzeInventoryRequest,
  ): Promise<import("@/types/cloudCost").CloudCostAnalyzeInventoryResponse> {
    const response = await apiClient.post(
      "/api/v1/cloud-cost-detector/analyze-inventory",
      { ...request, include_ai: request.include_ai ?? true },
      { timeout: 180_000 },
    );
    return response.data;
  },
};
