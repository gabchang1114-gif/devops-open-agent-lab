"use client";

import { useQuery } from "@tanstack/react-query";
import { investigationApi } from "@/services/investigationApi";
import { DEFAULT_CLUSTERS } from "@/types/investigation";

export function useClusters() {
  return useQuery({
    queryKey: ["clusters"],
    queryFn: () => investigationApi.listClusters(),
    staleTime: 30_000,
    retry: 1,
  });
}

export function useReadiness() {
  return useQuery({
    queryKey: ["system", "readiness"],
    queryFn: () => investigationApi.getReadiness(),
    refetchInterval: 15_000,
    retry: 1,
  });
}

export function resolveClusterOptions(
  clusters: Array<{ cluster_id: string; active: boolean }> | undefined,
): string[] {
  if (!clusters || clusters.length === 0) {
    return [...DEFAULT_CLUSTERS];
  }
  return clusters.map((cluster) => cluster.cluster_id);
}

export function resolveDefaultCluster(
  clusters: Array<{ cluster_id: string; active: boolean }> | undefined,
): string {
  const active = clusters?.find((cluster) => cluster.active);
  if (active) {
    return active.cluster_id;
  }
  if (clusters && clusters.length > 0) {
    return clusters[0].cluster_id;
  }
  return DEFAULT_CLUSTERS[0];
}
