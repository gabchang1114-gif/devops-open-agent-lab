export interface McpIntegrationSettings {
  enabled: boolean;
  server_url: string;
  api_key?: string | null;
  use_kubernetes: boolean;
  use_aws: boolean;
  use_cloud_cost: boolean;
  use_pr_reviewer: boolean;
}

export interface McpIntegrationResponse {
  enabled: boolean;
  server_url: string;
  api_key_configured: boolean;
  api_key_preview: string | null;
  use_kubernetes: boolean;
  use_aws: boolean;
  use_cloud_cost: boolean;
  use_pr_reviewer: boolean;
  instance_server_configured: boolean;
}

export interface McpTestResponse {
  status: string;
  message: string;
  tool_count: number;
  resource_count: number;
  tools: string[];
}

export interface McpToolCallRecord {
  tool_name: string;
  arguments: Record<string, unknown>;
  result_summary: string;
}

export interface McpAskRequest {
  question: string;
}

export interface McpAskResponse {
  answer: string;
  tools_used: McpToolCallRecord[];
}
