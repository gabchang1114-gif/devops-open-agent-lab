"use client";

import { useEffect, useState } from "react";
import { useMcpIntegration } from "@/hooks/useMcpIntegration";
import type { McpIntegrationSettings } from "@/types/mcpIntegration";
import { McpAskResultPanel } from "@/modules/integrations/McpAskResultPanel";

const AGENT_TOGGLES = [
  { key: "use_kubernetes" as const, label: "Kubernetes Debugging Agent" },
  { key: "use_aws" as const, label: "AWS DevOps Agent" },
  { key: "use_cloud_cost" as const, label: "Cloud Cost Detector" },
  { key: "use_pr_reviewer" as const, label: "PR Reviewer" },
];

function getErrorMessage(error: unknown): string {
  if (error && typeof error === "object" && "response" in error) {
    const axiosError = error as {
      response?: { data?: { detail?: unknown } };
      message?: string;
    };
    const detail = axiosError.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (axiosError.message && axiosError.message !== "Network Error") {
      return axiosError.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong.";
}

function buildFormState(
  settings: McpIntegrationSettings | undefined,
): McpIntegrationSettings {
  return {
    enabled: settings?.enabled ?? false,
    server_url: settings?.server_url ?? "",
    use_kubernetes: settings?.use_kubernetes ?? true,
    use_aws: settings?.use_aws ?? true,
    use_cloud_cost: settings?.use_cloud_cost ?? true,
    use_pr_reviewer: settings?.use_pr_reviewer ?? true,
  };
}

export function McpIntegrationPage() {
  const {
    settings,
    isLoading,
    saveSettings,
    isSaving,
    sendTest,
    isTesting,
    testResult,
    testError,
    saveError,
    askQuestion,
    isAsking,
    askResult,
    askError,
  } = useMcpIntegration();

  const [form, setForm] = useState<McpIntegrationSettings>(buildFormState(undefined));
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [question, setQuestion] = useState("");

  useEffect(() => {
    if (settings) {
      setForm(buildFormState(settings));
    }
  }, [settings]);

  const updateField = <K extends keyof McpIntegrationSettings>(
    key: K,
    value: McpIntegrationSettings[K],
  ) => {
    setForm((current) => ({ ...current, [key]: value }));
    setStatusMessage(null);
  };

  const handleSave = async () => {
    setStatusMessage(null);
    const payload: McpIntegrationSettings = {
      ...form,
      api_key: apiKeyInput.trim() ? apiKeyInput.trim() : null,
    };
    await saveSettings(payload);
    setApiKeyInput("");
    setStatusMessage("MCP settings saved.");
  };

  const handleTest = async () => {
    setStatusMessage(null);
    await sendTest();
  };

  const handleAsk = async () => {
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }
    await askQuestion(trimmed);
  };

  const mcpReady = Boolean(
    settings?.enabled &&
      (settings.server_url.trim() || settings.instance_server_configured),
  );

  if (isLoading) {
    return (
      <div className="panel rounded-2xl p-8 text-sm text-slate-400">
        Loading MCP integration settings...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="panel rounded-2xl p-6 sm:p-8">
        <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-white">MCP server</h2>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
              Connect a Model Context Protocol (MCP) server to query external tools directly or
              enrich AI investigations with discovered tools and resources.
            </p>
          </div>
          <label className="inline-flex cursor-pointer items-center gap-3 rounded-xl border border-white/[0.08] bg-slate-900/50 px-4 py-3">
            <span className="text-sm font-medium text-slate-200">Enable MCP</span>
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(event) => updateField("enabled", event.target.checked)}
              className="h-4 w-4 rounded border-white/20 bg-slate-900 text-brand-500 focus:ring-brand-500"
            />
          </label>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-5">
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-300">
                MCP server URL
              </label>
              <input
                type="url"
                value={form.server_url}
                onChange={(event) => updateField("server_url", event.target.value)}
                placeholder={
                  settings?.instance_server_configured
                    ? "https://your-mcp-server.example/mcp (or use instance default)"
                    : "https://your-mcp-server.example/mcp"
                }
                className="w-full rounded-xl border border-white/[0.08] bg-slate-900/70 px-4 py-3 font-mono text-sm text-white outline-none focus:border-brand-500/40"
              />
              <p className="mt-2 text-xs text-slate-500">
                Streamable HTTP endpoint for your MCP server (Events API v2 compatible).
              </p>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-300">
                API key (optional)
              </label>
              <input
                type="password"
                value={apiKeyInput}
                onChange={(event) => setApiKeyInput(event.target.value)}
                placeholder={
                  settings?.api_key_configured
                    ? `Configured ${settings.api_key_preview ?? ""}`
                    : "Bearer token for authenticated MCP servers"
                }
                className="w-full rounded-xl border border-white/[0.08] bg-slate-900/70 px-4 py-3 font-mono text-sm text-white outline-none focus:border-brand-500/40"
              />
              <p className="mt-2 text-xs text-slate-500">
                Sent as <span className="font-mono text-slate-400">Authorization: Bearer …</span>.
                Leave blank to keep the existing key.
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-5">
            <h3 className="text-sm font-semibold text-white">Use MCP for these agents</h3>
            <p className="mt-1 text-xs text-slate-500">
              When enabled, AI diagnosis will include tools and resources from your MCP server.
            </p>
            <div className="mt-4 space-y-3">
              {AGENT_TOGGLES.map((toggle) => (
                <label
                  key={toggle.key}
                  className="flex cursor-pointer items-center justify-between rounded-lg border border-white/[0.06] bg-slate-900/40 px-3 py-2.5"
                >
                  <span className="text-sm text-slate-300">{toggle.label}</span>
                  <input
                    type="checkbox"
                    checked={form[toggle.key]}
                    onChange={(event) => updateField(toggle.key, event.target.checked)}
                    className="h-4 w-4 rounded border-white/20 bg-slate-900 text-brand-500 focus:ring-brand-500"
                  />
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            className="rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-brand-500 disabled:opacity-60"
          >
            {isSaving ? "Saving..." : "Save settings"}
          </button>
          <button
            type="button"
            onClick={handleTest}
            disabled={isTesting}
            className="rounded-xl border border-white/[0.1] bg-slate-900/60 px-5 py-2.5 text-sm font-medium text-slate-200 transition hover:border-brand-500/30 hover:text-white disabled:opacity-60"
          >
            {isTesting ? "Testing..." : "Test connection"}
          </button>
        </div>

        {statusMessage && (
          <p className="mt-4 text-sm text-emerald-300">{statusMessage}</p>
        )}
        {testResult && (
          <div className="mt-4 space-y-2 text-sm text-emerald-300">
            <p>{testResult.message}</p>
            {testResult.tools.length > 0 && (
              <p className="text-slate-400">
                Sample tools: {testResult.tools.join(", ")}
              </p>
            )}
          </div>
        )}
        {(saveError || testError) && (
          <p className="mt-4 text-sm text-red-300">
            {getErrorMessage(saveError) || getErrorMessage(testError)}
          </p>
        )}
      </section>

      <section className="panel rounded-2xl p-6 sm:p-8">
        <div className="mb-4">
          <h2 className="text-xl font-semibold text-white">Ask MCP</h2>
          <p className="mt-2 max-w-2xl text-sm text-slate-400">
            Ask a question and DevOps Open Agent will call tools on your MCP server to find the
            answer. Works well with GitHub MCP — for example, list open pull requests or inspect a
            repository.
          </p>
        </div>

        <label className="block text-sm font-medium text-slate-300">
          Your question
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={4}
            disabled={!mcpReady || isAsking}
            placeholder={
              mcpReady
                ? "e.g. List open pull requests in ideaweaver-ai/devops-testing"
                : "Save MCP settings and enable the integration before asking questions."
            }
            className="mt-2 w-full rounded-xl border border-white/[0.08] bg-slate-900/70 px-4 py-3 text-sm text-white outline-none focus:border-brand-500/40 disabled:opacity-60"
          />
        </label>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleAsk}
            disabled={!mcpReady || isAsking || !question.trim()}
            className="rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-brand-500 disabled:opacity-60"
          >
            {isAsking ? "Asking..." : "Ask question"}
          </button>
          {!mcpReady && (
            <p className="text-xs text-slate-500">
              Enable MCP and save a server URL to use this feature.
            </p>
          )}
        </div>

        {askResult && <McpAskResultPanel result={askResult} />}

        {askError && (
          <p className="mt-4 text-sm text-red-300">{getErrorMessage(askError)}</p>
        )}
      </section>

      <section className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-6">
        <h2 className="text-lg font-semibold text-white">How it works</h2>
        <ul className="mt-4 space-y-3 text-sm text-slate-400">
          <li>
            Use <strong className="font-medium text-slate-300">Ask MCP</strong> to query your
            connected server directly with natural language.
          </li>
          <li>
            When enabled for agents below, DevOps Open Agent also discovers MCP tools before AI
            diagnosis and includes them in investigation context.
          </li>
          <li>
            Use <strong className="font-medium text-slate-300">Test connection</strong> to verify
            the URL and API key before asking questions or running investigations.
          </li>
          {settings?.instance_server_configured && (
            <li>
              An instance-level MCP server is configured and will be used as a fallback when you
              have not set a personal URL.
            </li>
          )}
        </ul>
      </section>
    </div>
  );
}
