"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { mcpIntegrationApi } from "@/services/mcpIntegrationApi";
import type {
  McpBlacklistCreate,
  McpIntegrationSettings,
  McpWhitelistCreate,
} from "@/types/mcpIntegration";

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

  const addWhitelistMutation = useMutation({
    mutationFn: (payload: McpWhitelistCreate) =>
      mcpIntegrationApi.addWhitelistEntry(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["mcp-integration"] });
    },
  });

  const removeWhitelistMutation = useMutation({
    mutationFn: (entryId: string) => mcpIntegrationApi.removeWhitelistEntry(entryId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["mcp-integration"] });
    },
  });

  const addBlacklistMutation = useMutation({
    mutationFn: (payload: McpBlacklistCreate) =>
      mcpIntegrationApi.addBlacklistEntry(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["mcp-integration"] });
    },
  });

  const removeBlacklistMutation = useMutation({
    mutationFn: (entryId: string) => mcpIntegrationApi.removeBlacklistEntry(entryId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["mcp-integration"] });
    },
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
    addWhitelistEntry: addWhitelistMutation.mutateAsync,
    isAddingWhitelist: addWhitelistMutation.isPending,
    addWhitelistError: addWhitelistMutation.error,
    removeWhitelistEntry: removeWhitelistMutation.mutateAsync,
    isRemovingWhitelist: removeWhitelistMutation.isPending,
    addBlacklistEntry: addBlacklistMutation.mutateAsync,
    isAddingBlacklist: addBlacklistMutation.isPending,
    addBlacklistError: addBlacklistMutation.error,
    removeBlacklistEntry: removeBlacklistMutation.mutateAsync,
    isRemovingBlacklist: removeBlacklistMutation.isPending,
  };
}
