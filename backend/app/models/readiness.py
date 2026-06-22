from pydantic import BaseModel


class SystemReadinessResponse(BaseModel):
    kubectl: bool
    kubeconfig: bool
    cluster_reachable: bool = False
    llm_provider: bool
    database: bool
