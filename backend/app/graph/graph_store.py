"""Graph store placeholder for future Neo4j integration."""


class GraphStore:
    """Placeholder interface for topology graph persistence."""

    async def connect(self) -> None:
        raise NotImplementedError("Graph store is not implemented yet.")

    async def upsert_node(self, node_type: str, node_id: str, properties: dict) -> None:
        raise NotImplementedError("Graph store is not implemented yet.")

    async def upsert_edge(self, source_id: str, target_id: str, relationship: str) -> None:
        raise NotImplementedError("Graph store is not implemented yet.")

    async def query_related_resources(self, resource_id: str) -> list[dict]:
        raise NotImplementedError("Graph store is not implemented yet.")
