"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import type { TopologyResult } from "@/types/topology";
import {
  AWS_LEGEND_ITEMS,
  detectTopologyVariant,
  edgePath,
  filterTopology,
  getKindStyles,
  getUniqueNamespaces,
  layoutTopology,
  summarizeTopology,
  type TopologyGraphVariant,
} from "@/lib/topologyLayout";

interface TopologyGraphProps {
  data: TopologyResult;
  compact?: boolean;
  height?: number;
  variant?: TopologyGraphVariant;
}

const K8S_LEGEND_ITEMS = ["ingress", "service", "deployment", "replicaset", "pod"] as const;
const HEADER_HEIGHT = 24;

export function TopologyGraph({ data, compact = false, height, variant }: TopologyGraphProps) {
  const resolvedVariant = variant ?? detectTopologyVariant(data);
  const legendItems =
    resolvedVariant === "aws" ? AWS_LEGEND_ITEMS : K8S_LEGEND_ITEMS;
  const scopeLabel = resolvedVariant === "aws" ? "Region" : "Namespace";
  const emptyMessage =
    resolvedVariant === "aws"
      ? "No AWS infrastructure relationships found for this region."
      : "No topology relationships found for this cluster.";
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [hoveredEdge, setHoveredEdge] = useState<string | null>(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const dragRef = useRef<{ x: number; y: number; panX: number; panY: number } | null>(null);

  const layout = useMemo(() => layoutTopology(data), [data]);
  const summary = useMemo(() => summarizeTopology(data), [data]);
  const nodeMap = useMemo(
    () => new Map(layout.nodes.map((node) => [node.id, node])),
    [layout.nodes],
  );

  const connectedEdges = useMemo(() => {
    if (!hoveredNode) {
      return new Set<string>();
    }
    return new Set(
      layout.edges
        .filter((edge) => edge.source === hoveredNode || edge.target === hoveredNode)
        .map((edge) => edge.id),
    );
  }, [hoveredNode, layout.edges]);

  const canvasHeight = height ?? (compact ? 380 : Math.max(layout.height, 560));

  const handleWheel = useCallback(
    (event: React.WheelEvent) => {
      if (compact) {
        return;
      }
      event.preventDefault();
      const delta = event.deltaY > 0 ? -0.08 : 0.08;
      setZoom((current) => Math.min(2, Math.max(0.45, current + delta)));
    },
    [compact],
  );

  const handlePointerDown = useCallback(
    (event: React.PointerEvent) => {
      if (compact || event.button !== 0) {
        return;
      }
      dragRef.current = {
        x: event.clientX,
        y: event.clientY,
        panX: pan.x,
        panY: pan.y,
      };
      event.currentTarget.setPointerCapture(event.pointerId);
    },
    [compact, pan.x, pan.y],
  );

  const handlePointerMove = useCallback((event: React.PointerEvent) => {
    if (!dragRef.current) {
      return;
    }
    setPan({
      x: dragRef.current.panX + (event.clientX - dragRef.current.x),
      y: dragRef.current.panY + (event.clientY - dragRef.current.y),
    });
  }, []);

  const handlePointerUp = useCallback((event: React.PointerEvent) => {
    dragRef.current = null;
    event.currentTarget.releasePointerCapture(event.pointerId);
  }, []);

  if (layout.nodes.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center rounded-xl border border-dashed border-white/[0.08] bg-slate-950/40 text-sm text-slate-400">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {!compact && (
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div className="flex flex-wrap gap-3">
            <StatPill label="Resources" value={String(summary.nodeCount)} />
            <StatPill label="Relationships" value={String(summary.edgeCount)} />
            <StatPill label={scopeLabel + "s"} value={String(summary.namespaceCount)} />
            {legendItems.map((kind) =>
              summary.kinds[kind] ? (
                <StatPill
                  key={kind}
                  label={kind.replace(/_/g, " ")}
                  value={String(summary.kinds[kind])}
                  kind={kind}
                />
              ) : null,
            )}
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <button
              type="button"
              onClick={() => {
                setZoom(1);
                setPan({ x: 0, y: 0 });
              }}
              className="rounded-lg border border-white/[0.08] px-3 py-1.5 text-slate-300 transition hover:bg-white/[0.04]"
            >
              Reset view
            </button>
            <span>Scroll to zoom · drag to pan</span>
          </div>
        </div>
      )}

      <div
        ref={containerRef}
        className={`relative overflow-hidden rounded-xl border border-white/[0.06] bg-[#050810] ${
          compact ? "cursor-default" : "cursor-grab active:cursor-grabbing"
        }`}
        style={{ height: canvasHeight }}
        onWheel={handleWheel}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
      >
        <div
          className="absolute inset-0 opacity-40"
          style={{
            backgroundImage:
              "radial-gradient(circle, rgba(148,163,184,0.22) 1px, transparent 1px)",
            backgroundSize: "18px 18px",
          }}
        />

        <svg
          width="100%"
          height="100%"
          className="relative block"
          role="img"
          aria-label={
            resolvedVariant === "aws" ? "AWS infrastructure topology graph" : "Cluster topology graph"
          }
        >
          <defs>
            <marker
              id="topology-arrow"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(203,213,225,0.75)" />
            </marker>
            <marker
              id="topology-arrow-active"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#60a5fa" />
            </marker>
          </defs>

          <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
            {layout.groups.map((group) => (
              <g key={group.id}>
                <rect
                  x={group.x}
                  y={group.y}
                  width={group.width}
                  height={group.height}
                  rx={18}
                  fill="rgba(88,28,135,0.05)"
                  stroke="rgba(168,85,247,0.28)"
                  strokeWidth={1.5}
                />
                <text
                  x={group.x + 20}
                  y={group.y + 26}
                  fill="#ddd6fe"
                  fontSize={13}
                  fontWeight={600}
                >
                  {scopeLabel} · {group.namespace}
                </text>
              </g>
            ))}

            {layout.stacks.map((stack) => (
              <g key={stack.id}>
                <rect
                  x={stack.x}
                  y={stack.y}
                  width={stack.width}
                  height={stack.height}
                  rx={14}
                  fill="rgba(249,115,22,0.04)"
                  stroke="rgba(249,115,22,0.22)"
                  strokeWidth={1.25}
                  strokeDasharray="4 3"
                />
                <text
                  x={stack.x + 14}
                  y={stack.y + 18}
                  fill="#fdba74"
                  fontSize={11}
                  fontWeight={600}
                >
                  Workload · {stack.label}
                </text>
              </g>
            ))}

            {layout.edges.map((edge) => {
              const source = nodeMap.get(edge.source);
              const target = nodeMap.get(edge.target);
              if (!source || !target) {
                return null;
              }

              const isActive =
                hoveredEdge === edge.id ||
                (hoveredNode ? connectedEdges.has(edge.id) : false);
              const path = edgePath(source, target);
              const midX = (source.x + source.width + target.x) / 2;
              const midY = (source.y + source.height / 2 + target.y + target.height / 2) / 2;

              return (
                <g
                  key={edge.id}
                  onMouseEnter={() => setHoveredEdge(edge.id)}
                  onMouseLeave={() => setHoveredEdge(null)}
                >
                  <path
                    d={path}
                    fill="none"
                    stroke={isActive ? "#60a5fa" : "rgba(203,213,225,0.42)"}
                    strokeWidth={isActive ? 2.5 : 1.5}
                    markerEnd={
                      isActive ? "url(#topology-arrow-active)" : "url(#topology-arrow)"
                    }
                  />
                  {(isActive || !compact) && (
                    <text
                      x={midX}
                      y={midY - 8}
                      textAnchor="middle"
                      fill={isActive ? "#93c5fd" : "#64748b"}
                      fontSize={10}
                      fontWeight={500}
                    >
                      {edge.label}
                    </text>
                  )}
                </g>
              );
            })}

            {layout.nodes.map((node) => {
              const styles = getKindStyles(node.kind);
              const isHovered = hoveredNode === node.id;
              const isConnected =
                hoveredNode && connectedEdges.size > 0
                  ? layout.edges.some(
                      (edge) =>
                        connectedEdges.has(edge.id) &&
                        (edge.source === node.id || edge.target === node.id),
                    )
                  : false;
              const dimmed = hoveredNode && !isHovered && !isConnected;
              const opacity = dimmed ? 0.28 : 1;

              return (
                <g
                  key={node.id}
                  opacity={opacity}
                  onMouseEnter={() => setHoveredNode(node.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  style={{ cursor: "pointer" }}
                >
                  <rect
                    x={node.x}
                    y={node.y}
                    width={node.width}
                    height={node.height}
                    rx={10}
                    fill="#0f172a"
                    stroke={isHovered ? "#60a5fa" : styles.accent}
                    strokeWidth={isHovered ? 2 : 1.25}
                    strokeOpacity={isHovered ? 1 : 0.55}
                  />
                  <rect
                    x={node.x}
                    y={node.y}
                    width={node.width}
                    height={HEADER_HEIGHT}
                    rx={10}
                    fill={styles.accent}
                    fillOpacity={0.22}
                  />
                  <rect
                    x={node.x}
                    y={node.y + HEADER_HEIGHT - 10}
                    width={node.width}
                    height={10}
                    fill={styles.accent}
                    fillOpacity={0.22}
                  />
                  <text
                    x={node.x + 10}
                    y={node.y + 16}
                    fill={styles.accent}
                    fontSize={10}
                    fontWeight={700}
                    letterSpacing="0.06em"
                  >
                    {node.label.toUpperCase()}
                  </text>
                  <text
                    x={node.x + 10}
                    y={node.y + 44}
                    fill="#e2e8f0"
                    fontSize={12}
                    fontFamily="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
                  >
                    {truncate(node.name, 26)}
                  </text>
                  <text
                    x={node.x + 10}
                    y={node.y + 60}
                    fill="#64748b"
                    fontSize={10}
                  >
                    {node.namespace}
                  </text>
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      {!compact && (
        <div className="flex flex-wrap gap-2">
          {legendItems.map((kind) => {
            const styles = getKindStyles(kind);
            return (
              <span
                key={kind}
                className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs capitalize ${styles.border}`}
              >
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: styles.accent }}
                />
                {kind.replace(/_/g, " ")}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}

function truncate(value: string, max: number): string {
  if (value.length <= max) {
    return value;
  }
  return `${value.slice(0, max - 1)}…`;
}

function StatPill({
  label,
  value,
  kind,
}: {
  label: string;
  value: string;
  kind?: string;
}) {
  const styles = kind ? getKindStyles(kind) : null;
  return (
    <div className="rounded-xl border border-white/[0.06] bg-slate-900/60 px-4 py-2">
      <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500">{label}</p>
      <p
        className="text-lg font-semibold tabular-nums"
        style={{ color: styles?.accent ?? "#e2e8f0" }}
      >
        {value}
      </p>
    </div>
  );
}

interface TopologyGraphPanelProps {
  data: TopologyResult;
  compact?: boolean;
  height?: number;
}

export function TopologyGraphPanel({ data, compact, height }: TopologyGraphPanelProps) {
  return <TopologyGraph data={data} compact={compact} height={height} />;
}

export { filterTopology, getUniqueNamespaces, summarizeTopology };
