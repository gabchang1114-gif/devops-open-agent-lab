import { apiClient } from "@/services/api";
import type {
  McpAskRequest,
  McpAskResponse,
  McpIntegrationResponse,
  McpIntegrationSettings,
  McpTestResponse,
} from "@/types/mcpIntegration";

export const mcpIntegrationApi = {
  async getSettings(): Promise<McpIntegrationResponse> {
    const response = await apiClient.get<McpIntegrationResponse>(
      "/api/v1/integrations/mcp",
    );
    return response.data;
  },

  async updateSettings(
    settings: McpIntegrationSettings,
  ): Promise<McpIntegrationResponse> {
    const response = await apiClient.put<McpIntegrationResponse>(
      "/api/v1/integrations/mcp",
      settings,
    );
    return response.data;
  },

  async sendTest(): Promise<McpTestResponse> {
    const response = await apiClient.post<McpTestResponse>(
      "/api/v1/integrations/mcp/test",
      undefined,
      { timeout: 120_000 },
    );
    return response.data;
  },

  async askQuestion(request: McpAskRequest): Promise<McpAskResponse> {
    const response = await apiClient.post<McpAskResponse>(
      "/api/v1/integrations/mcp/ask",
      request,
      { timeout: 180_000 },
    );
    return response.data;
  },
};
