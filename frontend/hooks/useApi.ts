"use client";

import { useQuery } from "@tanstack/react-query";
import { healthService, systemService } from "@/services";

export function useHealthCheck() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => healthService.getHealth(),
    enabled: false,
  });
}

export function useSystemInfo() {
  return useQuery({
    queryKey: ["system-info"],
    queryFn: () => systemService.getSystemInfo(),
    enabled: false,
  });
}
