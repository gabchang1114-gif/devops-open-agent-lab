from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.core.errors import sanitize_error_message
from app.kubernetes.kubeconfig_service import KubeconfigService
from app.models.auth import UserResponse
from app.models.clusters import ClusterItem, ClusterListResponse

router = APIRouter(tags=["clusters"])
kubeconfig_service = KubeconfigService()


@router.get("/clusters", response_model=ClusterListResponse)
async def list_clusters(
    _current_user: UserResponse = Depends(get_current_user),
) -> ClusterListResponse:
    clusters, error = kubeconfig_service.list_clusters()
    current_context = next((cluster.context for cluster in clusters if cluster.active), None)

    if error and not clusters:
        return ClusterListResponse(
            clusters=[],
            current_context=current_context,
            error=sanitize_error_message(error),
        )

    return ClusterListResponse(
        clusters=[
            ClusterItem(
                cluster_id=cluster.cluster_id,
                context=cluster.context,
                name=cluster.name,
                active=cluster.active,
            )
            for cluster in clusters
        ],
        current_context=current_context,
        error=sanitize_error_message(error) if error else None,
    )
