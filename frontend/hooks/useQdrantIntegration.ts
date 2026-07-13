"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { qdrantIntegrationApi } from "@/services/qdrantIntegrationApi";
import type { QdrantIntegrationSettings } from "@/types/qdrantIntegration";

export function useQdrantIntegration() {
  const queryClient = useQueryClient();

  const settingsQuery = useQuery({
    queryKey: ["qdrant-integration"],
    queryFn: () => qdrantIntegrationApi.getSettings(),
  });

  const saveMutation = useMutation({
    mutationFn: (settings: QdrantIntegrationSettings) =>
      qdrantIntegrationApi.updateSettings(settings),
    onSuccess: (data) => {
      queryClient.setQueryData(["qdrant-integration"], data);
    },
  });

  const testMutation = useMutation({
    mutationFn: () => qdrantIntegrationApi.sendTest(),
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
  };
}
