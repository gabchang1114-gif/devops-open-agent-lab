"use client";

import Link from "next/link";
import type { TopologyRelationship } from "@/types/topology";
import { TopologyGraph } from "@/components/topology/TopologyGraph";

interface TopologyPlaceholderProps {
  relationships?: TopologyRelationship[];
}

export function TopologyPlaceholder({ relationships = [] }: TopologyPlaceholderProps) {
  const hasData = relationships.length > 0;

  return (
    <div className="panel border-dashed border-white/[0.08] bg-slate-900/35 p-6">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/[0.08] bg-slate-800/60">
            <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 text-slate-400" aria-hidden>
              <circle cx="6" cy="6" r="2" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="18" cy="6" r="2" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="12" cy="18" r="2" stroke="currentColor" strokeWidth="1.5" />
              <path
                d="M8 6h8M7.5 7.5L10.5 16M16.5 7.5L13.5 16"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <div>
            <h2 className="panel-title">Topology Preview</h2>
            <p className="text-xs text-slate-500">
              {hasData
                ? `${relationships.length} relationships from the latest investigation`
                : "Run an investigation to collect relationships"}
            </p>
          </div>
        </div>
        <Link
          href="/topology"
          className="rounded-lg border border-brand-500/25 bg-brand-500/10 px-3 py-1.5 text-xs font-medium text-brand-300 transition hover:bg-brand-500/20"
        >
          Open full map →
        </Link>
      </div>

      {hasData ? (
        <TopologyGraph
          data={{
            relationships,
            nodes: Array.from(
              new Set(
                relationships.flatMap((relationship) => [
                  relationship.source,
                  relationship.target,
                ]),
              ),
            ),
          }}
          compact
        />
      ) : (
        <div className="rounded-xl border border-white/[0.06] bg-slate-950/60 p-8 text-center text-sm text-slate-400">
          Start an investigation to preview workload relationships here, or open the{" "}
          <Link href="/topology" className="text-brand-400 hover:text-brand-300">
            Topology tab
          </Link>{" "}
          to explore the full cluster map.
        </div>
      )}
    </div>
  );
}
