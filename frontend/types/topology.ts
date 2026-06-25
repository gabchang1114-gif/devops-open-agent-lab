export interface TopologyRelationship {
  source: string;
  target: string;
  type: string;
  namespace?: string | null;
}

export interface TopologyGraphNodeMeta {
  id: string;
  kind: string;
  name: string;
  namespace: string;
}

export interface TopologyResult {
  relationships: TopologyRelationship[];
  nodes: string[];
  graph_nodes?: TopologyGraphNodeMeta[];
}

export type TopologyResourceKind =
  | "namespace"
  | "deployment"
  | "replicaset"
  | "pod"
  | "service"
  | "ingress"
  | "endpoint"
  | "configmap"
  | "secret"
  | "vpc"
  | "subnet"
  | "internet_gateway"
  | "nat_gateway"
  | "route_table"
  | "network_acl"
  | "load_balancer"
  | "target_group"
  | "asg"
  | "ec2"
  | "lambda"
  | "s3"
  | "event_source"
  | "security_group"
  | "ebs"
  | "elastic_ip"
  | "iam_role"
  | "other";

export interface TopologyGraphNode {
  id: string;
  kind: TopologyResourceKind;
  name: string;
  namespace: string;
  label: string;
}

export interface TopologyGraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  label: string;
}

export interface TopologyLayoutNode extends TopologyGraphNode {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface TopologyLayoutGroup {
  id: string;
  namespace: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface TopologyLayoutStack {
  id: string;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface TopologyLayout {
  nodes: TopologyLayoutNode[];
  edges: TopologyGraphEdge[];
  groups: TopologyLayoutGroup[];
  stacks: TopologyLayoutStack[];
  width: number;
  height: number;
}
