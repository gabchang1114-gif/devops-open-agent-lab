"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { awsApi } from "@/services/awsApi";
import type { AwsInvestigationRequest } from "@/types/aws";

export function useAwsAccounts(region?: string, enabled = true) {
  return useQuery({
    queryKey: ["aws", "accounts", region ?? "default"],
    queryFn: () => awsApi.listAccounts(region),
    enabled,
    staleTime: 60_000,
    retry: 1,
  });
}

export function useAwsRegions(accountId: string, discoveryRegion?: string, enabled = true) {
  return useQuery({
    queryKey: ["aws", "regions", accountId, discoveryRegion ?? "default"],
    queryFn: () => awsApi.listRegions(accountId, discoveryRegion),
    enabled: Boolean(accountId) && enabled,
    staleTime: 60_000,
    retry: 1,
  });
}

export function useAwsInvestigation() {
  return useMutation({
    mutationFn: (request: AwsInvestigationRequest) => awsApi.investigate(request),
  });
}

export function useAwsTopology(accountId: string, region: string, enabled = true) {
  return useQuery({
    queryKey: ["aws", "topology", accountId, region],
    queryFn: () => awsApi.getTopology(accountId, region),
    enabled: Boolean(accountId) && Boolean(region) && enabled,
    staleTime: 60_000,
    retry: 1,
  });
}
