from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user
from app.core.errors import sanitize_error_message
from app.models.auth import UserResponse
from app.models.investigation import TopologyResult
from app.services.topology_service import TopologyService

router = APIRouter(tags=["topology"])
topology_service = TopologyService()


@router.get("/topology", response_model=TopologyResult)
async def get_cluster_topology(
    cluster_id: str = Query(..., description="Target cluster context"),
    namespace: str | None = Query(None, description="Optional namespace filter"),
    _current_user: UserResponse = Depends(get_current_user),
) -> TopologyResult:
    try:
        return await topology_service.get_topology(cluster_id, namespace=namespace)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=sanitize_error_message(str(exc)),
        ) from exc
