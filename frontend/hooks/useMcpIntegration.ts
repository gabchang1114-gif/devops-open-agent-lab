"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { mcpIntegrationApi } from "@/services/mcpIntegrationApi";
import type { McpIntegrationSettings } from "@/types/mcpIntegration";

export function useMcpIntegration() {
  const queryClient = useQueryClient();

  const settingsQuery = useQuery({
    queryKey: ["mcp-integration"],
    queryFn: () => mcpIntegrationApi.getSettings(),
  });

  const saveMutation = useMutation({
    mutationFn: (settings: McpIntegrationSettings) =>
      mcpIntegrationApi.updateSettings(settings),
    onSuccess: (data) => {
      queryClient.setQueryData(["mcp-integration"], data);
    },
  });

  const testMutation = useMutation({
    mutationFn: () => mcpIntegrationApi.sendTest(),
  });

  const askMutation = useMutation({
    mutationFn: (question: string) => mcpIntegrationApi.askQuestion({ question }),
  });

  return {
    settings: settingsQuery.data,
    isLoading: settingsQuery.isLoading,
    error: settingsQuery.error,
    saveSettings: saveMutation.mutateAsync,
    isSaving: saveMutation.isPending,
    saveError: saveMutation.error,
    sendTest: testMutation.mutateAsync,
    isTesting: testMutation.isPending,
    testResult: testMutation.data,
    testError: testMutation.error,
    askQuestion: askMutation.mutateAsync,
    isAsking: askMutation.isPending,
    askResult: askMutation.data,
    askError: askMutation.error,
  };
}
