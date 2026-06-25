import { apiClient } from "@/services/api";
import type {
  SlackIntegrationResponse,
  SlackIntegrationSettings,
  SlackTestResponse,
} from "@/types/slackIntegration";

export const slackIntegrationApi = {
  async getSettings(): Promise<SlackIntegrationResponse> {
    const response = await apiClient.get<SlackIntegrationResponse>(
      "/api/v1/integrations/slack",
    );
    return response.data;
  },

  async updateSettings(
    settings: SlackIntegrationSettings,
  ): Promise<SlackIntegrationResponse> {
    const response = await apiClient.put<SlackIntegrationResponse>(
      "/api/v1/integrations/slack",
      settings,
    );
    return response.data;
  },

  async sendTest(): Promise<SlackTestResponse> {
    const response = await apiClient.post<SlackTestResponse>(
      "/api/v1/integrations/slack/test",
    );
    return response.data;
  },
};
