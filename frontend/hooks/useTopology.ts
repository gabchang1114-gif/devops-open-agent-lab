"use client";

import { useQuery } from "@tanstack/react-query";
import { topologyApi } from "@/services/topologyApi";

export function useTopology(clusterId: string, namespace?: string, enabled = true) {
  return useQuery({
    queryKey: ["topology", clusterId, namespace ?? "all"],
    queryFn: () => topologyApi.getTopology(clusterId, namespace),
    enabled: Boolean(clusterId) && enabled,
    staleTime: 60_000,
    retry: 1,
  });
}
