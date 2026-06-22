"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { cloudCostApi } from "@/services/cloudCostApi";
import type { CloudCostAnalyzeRequest } from "@/types/cloudCost";

export function useCloudCostAccount(region?: string, enabled = true) {
  return useQuery({
    queryKey: ["cloud-cost", "account", region ?? "default"],
    queryFn: () => cloudCostApi.getAccount(region),
    enabled,
    staleTime: 60_000,
    retry: 1,
  });
}

export function useCloudCostRegions(region?: string, enabled = true) {
  return useQuery({
    queryKey: ["cloud-cost", "regions", region ?? "default"],
    queryFn: () => cloudCostApi.listRegions(region),
    enabled,
    staleTime: 60_000,
    retry: 1,
  });
}

export function useCloudCostAnalyze() {
  return useMutation({
    mutationFn: (request: CloudCostAnalyzeRequest) => cloudCostApi.analyze(request),
  });
}
