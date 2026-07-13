import { apiClient } from "@/services/api";
import type {
  McpAskRequest,
  McpAskResponse,
  McpBlacklistCreate,
  McpBlacklistEntry,
  McpIntegrationResponse,
  McpIntegrationSettings,
  McpTestResponse,
  McpWhitelistCreate,
  McpWhitelistEntry,
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

  async addWhitelistEntry(
    payload: McpWhitelistCreate,
  ): Promise<McpWhitelistEntry> {
    const response = await apiClient.post<McpWhitelistEntry>(
      "/api/v1/integrations/mcp/whitelist",
      payload,
    );
    return response.data;
  },

  async removeWhitelistEntry(entryId: string): Promise<void> {
    await apiClient.delete(`/api/v1/integrations/mcp/whitelist/${entryId}`);
  },

  async addBlacklistEntry(
    payload: McpBlacklistCreate,
  ): Promise<McpBlacklistEntry> {
    const response = await apiClient.post<McpBlacklistEntry>(
      "/api/v1/integrations/mcp/blacklist",
      payload,
    );
    return response.data;
  },

  async removeBlacklistEntry(entryId: string): Promise<void> {
    await apiClient.delete(`/api/v1/integrations/mcp/blacklist/${entryId}`);
  },
};
