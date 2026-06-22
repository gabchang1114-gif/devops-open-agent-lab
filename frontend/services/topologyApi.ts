import { apiClient } from "@/services/api";
import type { TopologyResult } from "@/types/topology";

export const topologyApi = {
  async getTopology(clusterId: string, namespace?: string): Promise<TopologyResult> {
    const response = await apiClient.get<TopologyResult>("/api/v1/topology", {
      params: {
        cluster_id: clusterId,
        namespace: namespace || undefined,
      },
    });
    return response.data;
  },
};
