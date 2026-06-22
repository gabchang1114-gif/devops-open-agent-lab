from pydantic import BaseModel, Field


class ClusterItem(BaseModel):
    cluster_id: str
    context: str
    name: str
    active: bool = False


class ClusterListResponse(BaseModel):
    clusters: list[ClusterItem] = Field(default_factory=list)
    current_context: str | None = None
    error: str | None = None
