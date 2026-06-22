"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { investigationApi } from "@/services/investigationApi";

export function useInvestigation() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: investigationApi.startInvestigation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["investigations", "history"] });
    },
  });

  return {
    startInvestigation: mutation.mutateAsync,
    isStarting: mutation.isPending,
    startError: mutation.error,
    reset: mutation.reset,
  };
}
