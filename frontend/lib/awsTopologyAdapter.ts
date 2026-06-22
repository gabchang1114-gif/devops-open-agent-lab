import type { AwsTopologyResult } from "@/types/aws";
import type { TopologyResult } from "@/types/topology";

export function awsTopologyToGraph(data: AwsTopologyResult): TopologyResult {
  return {
    relationships: data.relationships.map((relationship) => ({
      source: relationship.source,
      target: relationship.target,
      type: relationship.type,
      namespace: relationship.region ?? "default",
    })),
    nodes: data.nodes,
    graph_nodes: data.graph_nodes.map((node) => ({
      id: node.id,
      kind: node.kind,
      name: node.name,
      namespace: node.region,
    })),
  };
}
