"""Kubernetes investigation engine entry point."""

from app.models.diagnosis import InvestigationRequest
from app.models.investigation import InvestigationResponse
from app.services.investigation_service import InvestigationService


class KubernetesInvestigator:
    """Collect structured Kubernetes troubleshooting evidence."""

    def __init__(self, investigation_service: InvestigationService | None = None) -> None:
        self.investigation_service = investigation_service or InvestigationService()

    async def investigate(self, request: InvestigationRequest) -> InvestigationResponse:
        return await self.investigation_service.investigate(request)
