from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.models.auth import UserResponse
from app.models.diagnosis import DiagnoseRequest, DiagnoseResponse
from app.services.diagnosis_service import DiagnosisService

router = APIRouter(tags=["diagnosis"])
diagnosis_service = DiagnosisService()


@router.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose_investigation(
    request: DiagnoseRequest,
    _current_user: UserResponse = Depends(get_current_user),
) -> DiagnoseResponse:
    return await diagnosis_service.diagnose_payload(request.investigation_payload)
