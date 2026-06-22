from fastapi import APIRouter

from app.core.config import get_settings
from app.models.diagnosis import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version=settings.version,
    )
