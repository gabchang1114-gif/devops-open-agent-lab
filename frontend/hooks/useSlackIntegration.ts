"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { slackIntegrationApi } from "@/services/slackIntegrationApi";
import type { SlackIntegrationSettings } from "@/types/slackIntegration";

export function useSlackIntegration() {
  const queryClient = useQueryClient();

  const settingsQuery = useQuery({
    queryKey: ["slack-integration"],
    queryFn: () => slackIntegrationApi.getSettings(),
  });

  const saveMutation = useMutation({
    mutationFn: (settings: SlackIntegrationSettings) =>
      slackIntegrationApi.updateSettings(settings),
    onSuccess: (data) => {
      queryClient.setQueryData(["slack-integration"], data);
    },
  });

  const testMutation = useMutation({
    mutationFn: () => slackIntegrationApi.sendTest(),
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
