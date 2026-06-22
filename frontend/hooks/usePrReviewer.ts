"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { prReviewerApi } from "@/services/prReviewerApi";
import type { ManualReviewRequest } from "@/types/prReviewer";

export function usePrReviewHistory(enabled = true, limit = 50) {
  return useQuery({
    queryKey: ["pr-reviewer", "history", limit],
    queryFn: () => prReviewerApi.listHistory(limit),
    enabled,
    refetchInterval: 10_000,
  });
}

export function usePrReviewDetail(reviewId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["pr-reviewer", "review", reviewId],
    queryFn: () => prReviewerApi.getReview(reviewId!),
    enabled: Boolean(reviewId) && enabled,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status || status === "completed" || status === "failed") {
        return false;
      }
      return 2_000;
    },
  });
}

export function usePrReviewStatus(reviewId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["pr-reviewer", "status", reviewId],
    queryFn: () => prReviewerApi.getReviewStatus(reviewId!),
    enabled: Boolean(reviewId) && enabled,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status || status === "completed" || status === "failed") {
        return false;
      }
      return 2_000;
    },
  });
}

export function useStartPrReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: ManualReviewRequest) => prReviewerApi.startReview(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pr-reviewer", "history"] });
    },
  });
}
