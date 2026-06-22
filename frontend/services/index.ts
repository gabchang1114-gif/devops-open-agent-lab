import { apiClient } from "@/services/api";
import type { HealthResponse, SystemInfoResponse } from "@/types/api";

/**
 * Placeholder API service layer for future backend integration.
 */
export const healthService = {
  async getHealth(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>("/api/v1/health");
    return response.data;
  },

  async getRootHealth(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>("/health");
    return response.data;
  },
};

export const systemService = {
  async getSystemInfo(): Promise<SystemInfoResponse> {
    const response = await apiClient.get<SystemInfoResponse>("/api/v1/system/info");
    return response.data;
  },
};

export const investigationService = {
  async investigate(_clusterId: string, _query?: string): Promise<void> {
    throw new Error("Investigation workflows are not implemented yet.");
  },
};
