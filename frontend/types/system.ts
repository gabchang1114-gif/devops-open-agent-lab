export interface SystemReadinessResponse {
  kubectl: boolean;
  kubeconfig: boolean;
  cluster_reachable: boolean;
  llm_provider: boolean;
  database: boolean;
}

export interface ClusterItem {
  cluster_id: string;
  context: string;
  name: string;
  active: boolean;
}

export interface ClusterListResponse {
  clusters: ClusterItem[];
  current_context: string | null;
  error?: string | null;
}
