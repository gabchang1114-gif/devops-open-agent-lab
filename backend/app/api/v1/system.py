from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.core.config import get_settings
from app.core.readiness import ReadinessService
from app.models.auth import UserResponse
from app.models.diagnosis import SystemInfoResponse
from app.models.readiness import SystemReadinessResponse

router = APIRouter(tags=["system"])
readiness_service = ReadinessService()


@router.get("/system/info", response_model=SystemInfoResponse)
async def system_info(
    _current_user: UserResponse = Depends(get_current_user),
) -> SystemInfoResponse:
    settings = get_settings()
    return SystemInfoResponse(
        service=settings.service_name,
        environment=settings.app_env,
        llm_provider=settings.llm_provider,
        multi_cluster_enabled=settings.multi_cluster_enabled,
        topology_graph_enabled=settings.topology_graph_enabled,
        memory_enabled=settings.memory_enabled,
    )


@router.get("/system/readiness", response_model=SystemReadinessResponse)
async def system_readiness(
    _current_user: UserResponse = Depends(get_current_user),
) -> SystemReadinessResponse:
    checks = await readiness_service.check()
    return SystemReadinessResponse(**checks)
