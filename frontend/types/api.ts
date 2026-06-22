export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export interface SystemInfoResponse {
  service: string;
  environment: string;
  llm_provider: string;
  multi_cluster_enabled: boolean;
  topology_graph_enabled: boolean;
  memory_enabled: boolean;
}

export interface InvestigationRequest {
  cluster_id: string;
  namespace?: string;
  resource_type?: string;
  resource_name?: string;
  query?: string;
}
