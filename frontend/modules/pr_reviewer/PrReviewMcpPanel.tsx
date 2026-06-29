"use client";

interface McpTool {
  name: string;
  description?: string;
}

interface McpResource {
  name: string;
  uri: string;
  description?: string;
}

export interface PrReviewMcpEnrichment {
  connected?: boolean;
  server_url?: string;
  tool_count?: number;
  resource_count?: number;
  tools?: McpTool[];
  resources?: McpResource[];
  error?: string;
}

interface PrReviewMcpPanelProps {
  enrichment: PrReviewMcpEnrichment;
}

export function PrReviewMcpPanel({ enrichment }: PrReviewMcpPanelProps) {
  const connected = enrichment.connected !== false && !enrichment.error;
  const tools = enrichment.tools ?? [];
  const resources = enrichment.resources ?? [];

  return (
    <section className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white">MCP context</h3>
          <p className="mt-1 text-sm text-slate-400">
            External tools discovered from your MCP server and included in this review.
          </p>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-medium ${
            connected
              ? "bg-emerald-500/15 text-emerald-200"
              : "bg-red-500/15 text-red-200"
          }`}
        >
          {connected ? "Connected" : "Unavailable"}
        </span>
      </div>

      {enrichment.server_url && (
        <p className="mt-4 font-mono text-xs text-slate-500">{enrichment.server_url}</p>
      )}

      {enrichment.error && (
        <p className="mt-4 text-sm text-red-300">{enrichment.error}</p>
      )}

      {connected && (
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <div>
            <p className="text-sm font-medium text-slate-300">
              Tools ({enrichment.tool_count ?? tools.length})
            </p>
            {tools.length > 0 ? (
              <ul className="mt-3 max-h-56 space-y-2 overflow-y-auto text-sm">
                {tools.map((tool) => (
                  <li
                    key={tool.name}
                    className="rounded-lg border border-white/[0.06] bg-slate-900/40 px-3 py-2"
                  >
                    <p className="font-mono text-xs text-brand-200">{tool.name}</p>
                    {tool.description && (
                      <p className="mt-1 text-xs text-slate-500">{tool.description}</p>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-slate-500">No tools reported.</p>
            )}
          </div>

          <div>
            <p className="text-sm font-medium text-slate-300">
              Resources ({enrichment.resource_count ?? resources.length})
            </p>
            {resources.length > 0 ? (
              <ul className="mt-3 max-h-56 space-y-2 overflow-y-auto text-sm">
                {resources.map((resource) => (
                  <li
                    key={resource.uri}
                    className="rounded-lg border border-white/[0.06] bg-slate-900/40 px-3 py-2"
                  >
                    <p className="text-xs text-slate-200">{resource.name}</p>
                    <p className="mt-1 font-mono text-xs text-slate-500">{resource.uri}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-slate-500">No resources reported.</p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
