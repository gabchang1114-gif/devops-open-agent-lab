import { apiClient } from "@/services/api";
import type {
  QdrantIntegrationResponse,
  QdrantIntegrationSettings,
  QdrantTestResponse,
} from "@/types/qdrantIntegration";

export const qdrantIntegrationApi = {
  async getSettings(): Promise<QdrantIntegrationResponse> {
    const response = await apiClient.get<QdrantIntegrationResponse>(
      "/api/v1/integrations/qdrant",
    );
    return response.data;
  },

  async updateSettings(
    settings: QdrantIntegrationSettings,
  ): Promise<QdrantIntegrationResponse> {
    const response = await apiClient.put<QdrantIntegrationResponse>(
      "/api/v1/integrations/qdrant",
      settings,
    );
    return response.data;
  },

  async sendTest(): Promise<QdrantTestResponse> {
    const response = await apiClient.post<QdrantTestResponse>(
      "/api/v1/integrations/qdrant/test",
    );
    return response.data;
  },
};
