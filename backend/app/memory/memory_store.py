"""Memory store placeholder for future PostgreSQL/Redis integration."""


class MemoryStore:
    """Placeholder interface for persistent memory storage."""

    async def connect(self) -> None:
        raise NotImplementedError("Memory store is not implemented yet.")

    async def save(self, key: str, value: dict) -> None:
        raise NotImplementedError("Memory store is not implemented yet.")

    async def get(self, key: str) -> dict | None:
        raise NotImplementedError("Memory store is not implemented yet.")

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        raise NotImplementedError("Memory store is not implemented yet.")
