import type {
  TopologyGraphEdge,
  TopologyGraphNode,
  TopologyGraphNodeMeta,
  TopologyLayout,
  TopologyLayoutGroup,
  TopologyLayoutNode,
  TopologyLayoutStack,
  TopologyResourceKind,
  TopologyResult,
} from "@/types/topology";

const NODE_WIDTH = 228;
const NODE_HEIGHT = 68;
const NODE_GAP_X = 48;
const NODE_GAP_Y = 18;
const GROUP_PADDING = 32;
const GROUP_HEADER = 40;
const GROUP_GAP = 48;
const STACK_PADDING = 20;
const STACK_HEADER = 28;
const STACK_GAP = 24;

const AWS_KINDS = new Set([
  "vpc",
  "subnet",
  "internet_gateway",
  "nat_gateway",
  "route_table",
  "network_acl",
  "load_balancer",
  "target_group",
  "asg",
  "ec2",
  "lambda",
  "s3",
  "event_source",
  "security_group",
  "ebs",
  "elastic_ip",
  "iam_role",
]);

const AWS_COLUMN_KINDS: Record<string, number> = {
  vpc: 0,
  subnet: 0,
  internet_gateway: 0,
  nat_gateway: 0,
  route_table: 0,
  network_acl: 0,
  s3: 0,
  load_balancer: 1,
  target_group: 1,
  asg: 1,
  event_source: 1,
  ec2: 2,
  lambda: 2,
  ebs: 2,
  elastic_ip: 2,
  security_group: 3,
  iam_role: 3,
};


export const AWS_LEGEND_ITEMS = [
  "vpc",
  "subnet",
  "load_balancer",
  "target_group",
  "ec2",
  "lambda",
  "s3",
  "security_group",
] as const;

export type TopologyGraphVariant = "kubernetes" | "aws";

export function isAwsTopology(data: TopologyResult): boolean {
  const { nodes } = buildGraph(data);
  return nodes.some((node) => AWS_KINDS.has(node.kind));
}

export function detectTopologyVariant(data: TopologyResult): TopologyGraphVariant {
  return isAwsTopology(data) ? "aws" : "kubernetes";
}

const KIND_ORDER: Record<string, number> = {
  ingress: 0,
  service: 1,
  deployment: 2,
  replicaset: 3,
  pod: 4,
  namespace: -1,
  endpoint: 1,
  configmap: 5,
  secret: 5,
  other: 6,
  vpc: 0,
  subnet: 1,
  internet_gateway: 2,
  nat_gateway: 2,
  route_table: 3,
  network_acl: 3,
  load_balancer: 4,
  target_group: 5,
  asg: 6,
  ec2: 7,
  lambda: 7,
  s3: 6,
  event_source: 5,
  security_group: 8,
  ebs: 9,
  elastic_ip: 10,
  iam_role: 11,
};

export function parseResourceRef(ref: string): TopologyGraphNode {
  const [kindRaw, ...nameParts] = ref.split("/");
  const kind = normalizeKind(kindRaw);
  const name = nameParts.join("/") || ref;
  const namespace = kind === "namespace" ? name : "default";

  return {
    id: ref,
    kind,
    name,
    namespace,
    label: formatKindLabel(kind),
  };
}

function normalizeKind(kind: string): TopologyResourceKind {
  const normalized = kind.toLowerCase();
  if (normalized in KIND_ORDER) {
    return normalized as TopologyResourceKind;
  }
  return "other";
}

function formatKindLabel(kind: TopologyResourceKind): string {
  switch (kind) {
    case "replicaset":
      return "ReplicaSet";
    case "configmap":
      return "ConfigMap";
    case "internet_gateway":
      return "Internet Gateway";
    case "nat_gateway":
      return "NAT Gateway";
    case "route_table":
      return "Route Table";
    case "network_acl":
      return "Network ACL";
    case "load_balancer":
      return "Load Balancer";
    case "target_group":
      return "Target Group";
    case "security_group":
      return "Security Group";
    case "elastic_ip":
      return "Elastic IP";
    case "iam_role":
      return "IAM Role";
    case "lambda":
      return "Lambda";
    case "s3":
      return "S3 Bucket";
    case "event_source":
      return "Event Source";
    default:
      return kind.charAt(0).toUpperCase() + kind.slice(1);
  }
}

function nodeFromMeta(meta: TopologyGraphNodeMeta): TopologyGraphNode {
  const kind = normalizeKind(meta.kind);
  return {
    id: meta.id,
    kind,
    name: meta.name,
    namespace: meta.namespace || "default",
    label: formatKindLabel(kind),
  };
}

export function buildGraph(data: TopologyResult): {
  nodes: TopologyGraphNode[];
  edges: TopologyGraphEdge[];
} {
  const nodeMap = new Map<string, TopologyGraphNode>();

  if (data.graph_nodes?.length) {
    for (const meta of data.graph_nodes) {
      nodeMap.set(meta.id, nodeFromMeta(meta));
    }
  }

  for (const ref of data.nodes) {
    if (!nodeMap.has(ref)) {
      nodeMap.set(ref, parseResourceRef(ref));
    }
  }

  const edges: TopologyGraphEdge[] = data.relationships.map((relationship, index) => {
    if (!nodeMap.has(relationship.source)) {
      nodeMap.set(relationship.source, parseResourceRef(relationship.source));
    }
    if (!nodeMap.has(relationship.target)) {
      nodeMap.set(relationship.target, parseResourceRef(relationship.target));
    }

    const ns = relationship.namespace;
    if (ns) {
      const sourceNode = nodeMap.get(relationship.source);
      const targetNode = nodeMap.get(relationship.target);
      if (sourceNode && sourceNode.namespace === "default") {
        sourceNode.namespace = ns;
      }
      if (targetNode && targetNode.namespace === "default") {
        targetNode.namespace = ns;
      }
    }

    return {
      id: `edge-${index}-${relationship.source}-${relationship.target}`,
      source: relationship.source,
      target: relationship.target,
      type: relationship.type,
      label: relationship.type.replace(/_/g, " "),
    };
  });

  for (const edge of edges) {
    const sourceNode = nodeMap.get(edge.source);
    const targetNode = nodeMap.get(edge.target);
    if (sourceNode && targetNode) {
      if (sourceNode.namespace === "default" && targetNode.namespace !== "default") {
        sourceNode.namespace = targetNode.namespace;
      }
      if (targetNode.namespace === "default" && sourceNode.namespace !== "default") {
        targetNode.namespace = sourceNode.namespace;
      }
    }
  }

  const nodes = Array.from(nodeMap.values()).filter((node) => node.kind !== "namespace");
  return { nodes, edges };
}

interface WorkloadStack {
  id: string;
  deployment: TopologyGraphNode;
  replicaSets: TopologyGraphNode[];
  pods: TopologyGraphNode[];
}

function findWorkloadStacks(
  namespaceNodes: TopologyGraphNode[],
  edges: TopologyGraphEdge[],
): { stacks: WorkloadStack[]; standalone: TopologyGraphNode[] } {
  const nodeById = new Map(namespaceNodes.map((node) => [node.id, node]));
  const inStack = new Set<string>();
  const stacks: WorkloadStack[] = [];

  const deployments = namespaceNodes
    .filter((node) => node.kind === "deployment")
    .sort((a, b) => a.name.localeCompare(b.name));

  for (const deployment of deployments) {
    const replicaSets = edges
      .filter(
        (edge) =>
          edge.source === deployment.id &&
          edge.type === "owns" &&
          nodeById.get(edge.target)?.kind === "replicaset",
      )
      .map((edge) => nodeById.get(edge.target)!)
      .filter(Boolean);

    const rsIds = new Set(replicaSets.map((rs) => rs.id));
    const pods = edges
      .filter((edge) => {
        if (edge.type !== "owns") {
          return false;
        }
        const target = nodeById.get(edge.target);
        if (!target || target.kind !== "pod") {
          return false;
        }
        return edge.source === deployment.id || rsIds.has(edge.source);
      })
      .map((edge) => nodeById.get(edge.target)!)
      .filter(Boolean);

    const members = [deployment, ...replicaSets, ...pods];
    if (members.length > 1) {
      for (const member of members) {
        inStack.add(member.id);
      }
      stacks.push({
        id: `stack-${deployment.id}`,
        deployment,
        replicaSets,
        pods,
      });
    }
  }

  const standalone = namespaceNodes.filter((node) => !inStack.has(node.id));
  return { stacks, standalone };
}

function layoutStack(
  stack: WorkloadStack,
  x: number,
  y: number,
): { stack: TopologyLayoutStack; nodes: TopologyLayoutNode[] } {
  const stackNodes: TopologyGraphNode[] = [
    stack.deployment,
    ...stack.replicaSets,
    ...stack.pods,
  ];

  const innerWidth = NODE_WIDTH;
  const innerHeight =
    stackNodes.length * NODE_HEIGHT + Math.max(stackNodes.length - 1, 0) * NODE_GAP_Y;
  const stackWidth = innerWidth + STACK_PADDING * 2;
  const stackHeight = innerHeight + STACK_PADDING * 2 + STACK_HEADER;

  const layoutNodes: TopologyLayoutNode[] = stackNodes.map((node, index) => ({
    ...node,
    x: x + STACK_PADDING,
    y: y + STACK_HEADER + STACK_PADDING + index * (NODE_HEIGHT + NODE_GAP_Y),
    width: NODE_WIDTH,
    height: NODE_HEIGHT,
  }));

  return {
    stack: {
      id: stack.id,
      label: stack.deployment.name,
      x,
      y,
      width: stackWidth,
      height: stackHeight,
    },
    nodes: layoutNodes,
  };
}

export function layoutTopology(data: TopologyResult): TopologyLayout {
  if (isAwsTopology(data)) {
    return layoutAwsTopology(data);
  }
  return layoutKubernetesTopology(data);
}

function layoutAwsTopology(data: TopologyResult): TopologyLayout {
  const { nodes, edges } = buildGraph(data);
  const regions = Array.from(new Set(nodes.map((node) => node.namespace))).sort();

  const groups: TopologyLayoutGroup[] = [];
  const layoutNodes: TopologyLayoutNode[] = [];
  let offsetY = 48;

  for (const region of regions) {
    const regionNodes = nodes.filter((node) => node.namespace === region);
    if (regionNodes.length === 0) {
      continue;
    }

    const columns: TopologyGraphNode[][] = [[], [], [], []];
    for (const node of regionNodes) {
      const columnIndex = AWS_COLUMN_KINDS[node.kind] ?? 2;
      columns[columnIndex].push(node);
    }

    for (const column of columns) {
      column.sort((a, b) => {
        const kindDiff = (KIND_ORDER[a.kind] ?? 99) - (KIND_ORDER[b.kind] ?? 99);
        if (kindDiff !== 0) {
          return kindDiff;
        }
        return a.name.localeCompare(b.name);
      });
    }

    const groupX = 56;
    const groupY = offsetY;
    const contentStartY = groupY + GROUP_HEADER + GROUP_PADDING;
    const columnLayouts: TopologyLayoutNode[][] = columns.map((columnNodes, columnIndex) => {
      const columnX = groupX + GROUP_PADDING + columnIndex * (NODE_WIDTH + NODE_GAP_X);
      return columnNodes.map((node, rowIndex) => ({
        ...node,
        x: columnX,
        y: contentStartY + rowIndex * (NODE_HEIGHT + NODE_GAP_Y),
        width: NODE_WIDTH,
        height: NODE_HEIGHT,
      }));
    });

    const allPlaced = columnLayouts.flat();
    layoutNodes.push(...allPlaced);

    const maxColumnBottom = Math.max(
      ...allPlaced.map((node) => node.y + node.height),
      contentStartY,
    );
    const rightEdge = Math.max(
      ...allPlaced.map((node) => node.x + node.width),
      groupX + GROUP_PADDING + NODE_WIDTH,
    );

    const groupInnerHeight = maxColumnBottom - contentStartY + GROUP_PADDING;
    const groupWidth = rightEdge - groupX + GROUP_PADDING;
    const groupHeight = groupInnerHeight + GROUP_HEADER + GROUP_PADDING * 2;

    groups.push({
      id: `group-${region}`,
      namespace: region,
      x: groupX,
      y: groupY,
      width: groupWidth,
      height: groupHeight,
    });

    offsetY += groupHeight + GROUP_GAP;
  }

  const maxNodeX = layoutNodes.reduce(
    (max, node) => Math.max(max, node.x + node.width),
    0,
  );
  const width = Math.max(maxNodeX, 960) + 120;
  const height = Math.max(offsetY + 48, 520);

  return {
    nodes: layoutNodes,
    edges,
    groups,
    stacks: [],
    width,
    height,
  };
}

function layoutKubernetesTopology(data: TopologyResult): TopologyLayout {
  const { nodes, edges } = buildGraph(data);
  const namespaces = Array.from(new Set(nodes.map((node) => node.namespace))).sort();

  const groups: TopologyLayoutGroup[] = [];
  const stacks: TopologyLayoutStack[] = [];
  const layoutNodes: TopologyLayoutNode[] = [];
  let offsetY = 48;

  for (const namespace of namespaces) {
    const namespaceNodes = nodes.filter((node) => node.namespace === namespace);
    if (namespaceNodes.length === 0) {
      continue;
    }

    const { stacks: workloadStacks, standalone } = findWorkloadStacks(namespaceNodes, edges);

    const ingressNodes = standalone
      .filter((node) => node.kind === "ingress")
      .sort((a, b) => a.name.localeCompare(b.name));
    const serviceNodes = standalone
      .filter((node) => node.kind === "service")
      .sort((a, b) => a.name.localeCompare(b.name));
    const otherStandalone = standalone
      .filter((node) => node.kind !== "ingress" && node.kind !== "service")
      .sort((a, b) => {
        const kindDiff = KIND_ORDER[a.kind] - KIND_ORDER[b.kind];
        if (kindDiff !== 0) {
          return kindDiff;
        }
        return a.name.localeCompare(b.name);
      });

    const placeColumn = (
      columnNodes: TopologyGraphNode[],
      startY: number,
      columnX: number,
    ): TopologyLayoutNode[] =>
      columnNodes.map((node, rowIndex) => ({
        ...node,
        x: columnX,
        y: startY + rowIndex * (NODE_HEIGHT + NODE_GAP_Y),
        width: NODE_WIDTH,
        height: NODE_HEIGHT,
      }));

    const groupX = 56;
    const groupY = offsetY;
    const contentStartY = groupY + GROUP_HEADER + GROUP_PADDING;
    const col0X = groupX + GROUP_PADDING;
    const col1X = col0X + NODE_WIDTH + NODE_GAP_X;

    const ingressLayouts = placeColumn(ingressNodes, contentStartY, col0X);
    const serviceLayouts = placeColumn(serviceNodes, contentStartY, col1X);

    let stackX = col1X + NODE_WIDTH + NODE_GAP_X;
    const stackLayouts: TopologyLayoutNode[] = [];
    let stackCursorY = contentStartY;
    let maxStackRight = stackX;

    for (const workloadStack of workloadStacks) {
      const { stack: stackBox, nodes: stackNodeLayouts } = layoutStack(
        workloadStack,
        stackX,
        stackCursorY,
      );
      stacks.push(stackBox);
      stackLayouts.push(...stackNodeLayouts);
      maxStackRight = Math.max(maxStackRight, stackBox.x + stackBox.width);
      stackCursorY += stackBox.height + STACK_GAP;
    }

    const otherColumnX =
      workloadStacks.length > 0 ? maxStackRight + NODE_GAP_X : stackX;
    const otherLayouts = otherStandalone.map((node, rowIndex) => ({
      ...node,
      x: otherColumnX,
      y: contentStartY + rowIndex * (NODE_HEIGHT + NODE_GAP_Y),
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
    }));

    const allPlaced = [
      ...ingressLayouts,
      ...serviceLayouts,
      ...stackLayouts,
      ...otherLayouts,
    ];
    layoutNodes.push(...allPlaced);

    const maxColumnBottom = Math.max(
      ...allPlaced.map((node) => node.y + node.height),
      contentStartY,
    );
    const rightEdge = Math.max(
      ...allPlaced.map((node) => node.x + node.width),
      maxStackRight,
      col1X + NODE_WIDTH,
    );

    const groupInnerHeight = maxColumnBottom - contentStartY + GROUP_PADDING;
    const groupWidth = rightEdge - groupX + GROUP_PADDING;
    const groupHeight = groupInnerHeight + GROUP_HEADER + GROUP_PADDING * 2;

    groups.push({
      id: `group-${namespace}`,
      namespace,
      x: groupX,
      y: groupY,
      width: groupWidth,
      height: groupHeight,
    });

    offsetY += groupHeight + GROUP_GAP;
  }

  const maxNodeX = layoutNodes.reduce(
    (max, node) => Math.max(max, node.x + node.width),
    0,
  );
  const maxStackX = stacks.reduce((max, stack) => Math.max(max, stack.x + stack.width), 0);
  const width = Math.max(maxNodeX, maxStackX) + 120;
  const height = Math.max(offsetY + 48, 520);

  return {
    nodes: layoutNodes,
    edges,
    groups,
    stacks,
    width,
    height,
  };
}

export function getUniqueNamespaces(data: TopologyResult): string[] {
  const { nodes } = buildGraph(data);
  return Array.from(new Set(nodes.map((node) => node.namespace))).sort();
}

export function getUniqueVpcs(data: TopologyResult): Array<{ id: string; name: string }> {
  const { nodes } = buildGraph(data);
  return nodes
    .filter((node) => node.kind === "vpc")
    .map((node) => ({ id: node.id, name: node.name }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

export function filterAwsTopologyByVpc(
  data: TopologyResult,
  vpcRef: string | null,
): TopologyResult {
  if (!vpcRef || vpcRef === "all") {
    return data;
  }

  const nodeIds = new Set<string>([vpcRef]);
  let changed = true;
  while (changed) {
    changed = false;
    for (const relationship of data.relationships) {
      if (nodeIds.has(relationship.source) && !nodeIds.has(relationship.target)) {
        nodeIds.add(relationship.target);
        changed = true;
      }
      if (nodeIds.has(relationship.target) && !nodeIds.has(relationship.source)) {
        nodeIds.add(relationship.source);
        changed = true;
      }
    }
  }

  const relationships = data.relationships.filter(
    (relationship) => nodeIds.has(relationship.source) && nodeIds.has(relationship.target),
  );

  return {
    relationships,
    nodes: data.nodes.filter((node) => nodeIds.has(node)),
    graph_nodes: data.graph_nodes?.filter((node) => nodeIds.has(node.id)),
  };
}

export function filterTopology(
  data: TopologyResult,
  namespace: string | null,
): TopologyResult {
  if (!namespace || namespace === "all") {
    return data;
  }

  const namespaceNodeIds = new Set<string>();
  for (const meta of data.graph_nodes ?? []) {
    if ((meta.namespace || "default") === namespace) {
      namespaceNodeIds.add(meta.id);
    }
  }

  const relationships = data.relationships.filter((relationship) => {
    if (relationship.namespace && relationship.namespace !== namespace) {
      return false;
    }
    return (
      namespaceNodeIds.has(relationship.source) || namespaceNodeIds.has(relationship.target)
    );
  });

  const nodeIds = new Set(namespaceNodeIds);
  for (const relationship of relationships) {
    nodeIds.add(relationship.source);
    nodeIds.add(relationship.target);
  }

  const scopedRelationships = relationships.filter(
    (relationship) => nodeIds.has(relationship.source) && nodeIds.has(relationship.target),
  );

  return {
    relationships: scopedRelationships,
    nodes: data.nodes.filter((node) => nodeIds.has(node)),
    graph_nodes: data.graph_nodes?.filter((node) => nodeIds.has(node.id)),
  };
}

export function getKindStyles(kind: string): {
  border: string;
  background: string;
  header: string;
  badge: string;
  accent: string;
} {
  switch (kind) {
    case "ingress":
      return {
        border: "border-fuchsia-500/35",
        background: "bg-[#1a1025]",
        header: "bg-fuchsia-600/25",
        badge: "text-fuchsia-200",
        accent: "#d946ef",
      };
    case "service":
      return {
        border: "border-sky-500/35",
        background: "bg-[#0c1524]",
        header: "bg-sky-600/25",
        badge: "text-sky-200",
        accent: "#0ea5e9",
      };
    case "deployment":
      return {
        border: "border-orange-500/35",
        background: "bg-[#1a1208]",
        header: "bg-orange-600/25",
        badge: "text-orange-200",
        accent: "#f97316",
      };
    case "replicaset":
      return {
        border: "border-amber-500/35",
        background: "bg-[#1a1508]",
        header: "bg-amber-600/25",
        badge: "text-amber-200",
        accent: "#f59e0b",
      };
    case "pod":
      return {
        border: "border-emerald-500/35",
        background: "bg-[#081a12]",
        header: "bg-emerald-600/25",
        badge: "text-emerald-200",
        accent: "#10b981",
      };
    case "ec2":
      return {
        border: "border-orange-500/35",
        background: "bg-[#1a1208]",
        header: "bg-orange-600/25",
        badge: "text-orange-200",
        accent: "#f97316",
      };
    case "vpc":
      return {
        border: "border-violet-500/35",
        background: "bg-[#151025]",
        header: "bg-violet-600/25",
        badge: "text-violet-200",
        accent: "#8b5cf6",
      };
    case "subnet":
      return {
        border: "border-indigo-500/35",
        background: "bg-[#0f1224]",
        header: "bg-indigo-600/25",
        badge: "text-indigo-200",
        accent: "#6366f1",
      };
    case "security_group":
      return {
        border: "border-rose-500/35",
        background: "bg-[#1a0f12]",
        header: "bg-rose-600/25",
        badge: "text-rose-200",
        accent: "#f43f5e",
      };
    case "load_balancer":
      return {
        border: "border-cyan-500/35",
        background: "bg-[#081a1f]",
        header: "bg-cyan-600/25",
        badge: "text-cyan-200",
        accent: "#06b6d4",
      };
    case "target_group":
      return {
        border: "border-teal-500/35",
        background: "bg-[#081a18]",
        header: "bg-teal-600/25",
        badge: "text-teal-200",
        accent: "#14b8a6",
      };
    case "asg":
      return {
        border: "border-amber-500/35",
        background: "bg-[#1a1508]",
        header: "bg-amber-600/25",
        badge: "text-amber-200",
        accent: "#f59e0b",
      };
    case "internet_gateway":
    case "nat_gateway":
      return {
        border: "border-violet-500/35",
        background: "bg-[#151025]",
        header: "bg-violet-600/25",
        badge: "text-violet-200",
        accent: "#8b5cf6",
      };
    case "route_table":
    case "network_acl":
      return {
        border: "border-indigo-500/35",
        background: "bg-[#0f1224]",
        header: "bg-indigo-600/25",
        badge: "text-indigo-200",
        accent: "#6366f1",
      };
    case "elastic_ip":
      return {
        border: "border-yellow-500/35",
        background: "bg-[#1a1808]",
        header: "bg-yellow-600/25",
        badge: "text-yellow-200",
        accent: "#eab308",
      };
    case "iam_role":
      return {
        border: "border-pink-500/35",
        background: "bg-[#1a0f18]",
        header: "bg-pink-600/25",
        badge: "text-pink-200",
        accent: "#ec4899",
      };
    case "ebs":
      return {
        border: "border-lime-500/35",
        background: "bg-[#121a08]",
        header: "bg-lime-600/25",
        badge: "text-lime-200",
        accent: "#84cc16",
      };
    case "lambda":
      return {
        border: "border-orange-500/35",
        background: "bg-[#1a1208]",
        header: "bg-orange-600/25",
        badge: "text-orange-200",
        accent: "#f97316",
      };
    case "s3":
      return {
        border: "border-green-500/35",
        background: "bg-[#081a0f]",
        header: "bg-green-600/25",
        badge: "text-green-200",
        accent: "#22c55e",
      };
    case "event_source":
      return {
        border: "border-teal-500/35",
        background: "bg-[#081a18]",
        header: "bg-teal-600/25",
        badge: "text-teal-200",
        accent: "#14b8a6",
      };
    default:
      return {
        border: "border-slate-500/35",
        background: "bg-[#111827]",
        header: "bg-slate-600/25",
        badge: "text-slate-200",
        accent: "#64748b",
      };
  }
}

export function edgePath(
  source: TopologyLayoutNode,
  target: TopologyLayoutNode,
): string {
  const startX = source.x + source.width;
  const startY = source.y + source.height / 2;
  const endX = target.x;
  const endY = target.y + target.height / 2;
  const deltaX = endX - startX;

  if (deltaX < 40) {
    const midY = (startY + endY) / 2;
    return `M ${startX} ${startY} L ${startX + 20} ${startY} L ${startX + 20} ${midY} L ${endX - 20} ${midY} L ${endX - 20} ${endY} L ${endX} ${endY}`;
  }

  const midX = startX + deltaX * 0.55;
  return `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`;
}

export function summarizeTopology(data: TopologyResult) {
  const { nodes, edges } = buildGraph(data);
  const kinds = nodes.reduce<Record<string, number>>((acc, node) => {
    acc[node.kind] = (acc[node.kind] ?? 0) + 1;
    return acc;
  }, {});

  return {
    nodeCount: nodes.length,
    edgeCount: edges.length,
    namespaceCount: getUniqueNamespaces(data).length,
    kinds,
  };
}
