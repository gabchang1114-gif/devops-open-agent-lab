"use client";

import { useMemo, useState } from "react";
import type { McpAskResponse } from "@/types/mcpIntegration";

function InlineMarkdown({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <>
      {parts.map((part, index) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return (
            <strong key={index} className="font-semibold text-white">
              {part.slice(2, -2)}
            </strong>
          );
        }
        return <span key={index}>{part}</span>;
      })}
    </>
  );
}

function McpAnswerBody({ text }: { text: string }) {
  const blocks = useMemo(() => text.split(/\n\n+/).filter(Boolean), [text]);

  return (
    <div className="space-y-3">
      {blocks.map((block, blockIndex) => {
        const lines = block.split("\n").filter((line) => line.trim());
        const isList = lines.length > 0 && lines.every((line) => /^\s*[*-]\s+/.test(line));

        if (isList) {
          return (
            <ul key={blockIndex} className="space-y-2 pl-1">
              {lines.map((line, lineIndex) => (
                <li
                  key={lineIndex}
                  className="flex gap-2 text-sm leading-relaxed text-slate-200"
                >
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-400" />
                  <span>
                    <InlineMarkdown text={line.replace(/^\s*[*-]\s+/, "")} />
                  </span>
                </li>
              ))}
            </ul>
          );
        }

        return (
          <p key={blockIndex} className="text-sm leading-relaxed text-slate-200">
            <InlineMarkdown text={block} />
          </p>
        );
      })}
    </div>
  );
}

interface PullRequestSummary {
  number: number;
  title: string;
  html_url?: string;
  user?: { login?: string };
  state?: string;
}

function isPullRequestList(value: unknown): value is PullRequestSummary[] {
  return (
    Array.isArray(value) &&
    value.length > 0 &&
    typeof value[0] === "object" &&
    value[0] !== null &&
    "number" in value[0] &&
    "title" in value[0]
  );
}

function ToolResultBody({
  toolName,
  raw,
}: {
  toolName: string;
  raw: string;
}) {
  const [expanded, setExpanded] = useState(false);

  const parsed = useMemo(() => {
    try {
      return JSON.parse(raw) as unknown;
    } catch {
      const arrayMatch = raw.match(/\[[\s\S]*\]/);
      if (arrayMatch) {
        try {
          return JSON.parse(arrayMatch[0]) as unknown;
        } catch {
          return null;
        }
      }
      return null;
    }
  }, [raw]);

  if (isPullRequestList(parsed)) {
    return (
      <div className="mt-3 overflow-hidden rounded-xl border border-white/[0.06]">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900/60 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-3 py-2 font-medium">PR</th>
              <th className="px-3 py-2 font-medium">Title</th>
              <th className="px-3 py-2 font-medium">Author</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.06]">
            {parsed.map((pr) => (
              <tr key={pr.number} className="bg-slate-900/30">
                <td className="px-3 py-2 font-mono text-brand-200">
                  {pr.html_url ? (
                    <a
                      href={pr.html_url}
                      target="_blank"
                      rel="noreferrer"
                      className="hover:underline"
                    >
                      #{pr.number}
                    </a>
                  ) : (
                    `#${pr.number}`
                  )}
                </td>
                <td className="px-3 py-2 text-slate-200">{pr.title}</td>
                <td className="px-3 py-2 text-slate-400">{pr.user?.login ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  const pretty = parsed ? JSON.stringify(parsed, null, 2) : raw.trim();
  const isLong = pretty.length > 600;

  return (
    <div className="mt-3">
      {parsed === null && (
        <p className="text-sm leading-relaxed text-slate-400 whitespace-pre-wrap">{raw}</p>
      )}
      {parsed !== null && (
        <>
          <pre
            className={`overflow-x-auto rounded-xl border border-white/[0.06] bg-slate-950/80 p-3 font-mono text-xs leading-relaxed text-slate-400 ${
              !expanded && isLong ? "max-h-40" : "max-h-[28rem]"
            }`}
          >
            {pretty}
          </pre>
          {isLong && (
            <button
              type="button"
              onClick={() => setExpanded((current) => !current)}
              className="mt-2 text-xs font-medium text-brand-200 hover:underline"
            >
              {expanded ? "Show less" : `Show full ${toolName} output`}
            </button>
          )}
        </>
      )}
    </div>
  );
}

export function McpAskResultPanel({ result }: { result: McpAskResponse }) {
  return (
    <div className="mt-6 space-y-5 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5">
      <div>
        <h3 className="text-sm font-semibold text-emerald-100">Answer</h3>
        <div className="mt-3">
          <McpAnswerBody text={result.answer} />
        </div>
      </div>

      {result.tools_used.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Tools used
          </h4>
          {result.tools_used.map((tool, index) => (
            <details
              key={`${tool.tool_name}-${index}`}
              className="group rounded-xl border border-white/[0.06] bg-slate-900/40"
              open={result.tools_used.length === 1}
            >
              <summary className="cursor-pointer list-none px-4 py-3 text-sm marker:content-none [&::-webkit-details-marker]:hidden">
                <span className="font-mono text-brand-200">{tool.tool_name}</span>
              </summary>
              <div className="border-t border-white/[0.06] px-4 pb-4">
                <ToolResultBody toolName={tool.tool_name} raw={tool.result_summary} />
              </div>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}
