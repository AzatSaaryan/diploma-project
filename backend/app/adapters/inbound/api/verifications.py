from typing import Annotated

from fastapi import APIRouter, Depends, Path, UploadFile

from app.adapters.inbound.api.deps import (
    SettingsDep,
    get_document_status,
    get_verify_document,
    read_upload,
)
from app.adapters.inbound.api.schemas import VerificationResponse
from app.application.use_cases.get_document_status import GetDocumentStatus
from app.application.use_cases.resolve_status import VerificationResult
from app.application.use_cases.verify_document import VerifyDocument

router = APIRouter(prefix="/verifications", tags=["verifications"])

DocumentId = Annotated[str, Path(pattern=r"^[0-9a-f]{32}$")]


def _to_response(result: VerificationResult) -> VerificationResponse:
    record = result.record
    return VerificationResponse(
        status=result.status,
        document_id=result.document_id,
        issuer=record.issuer if record else None,
        issued_at=record.issued_at if record else None,
        expires_at=record.expires_at if record else None,
    )


@router.post("")
async def verify_file(
    file: UploadFile,
    settings: SettingsDep,
    use_case: Annotated[VerifyDocument, Depends(get_verify_document)],
) -> VerificationResponse:
    result = await use_case.execute(await read_upload(file, settings))
    return _to_response(result)


@router.get("/{document_id}")
async def verify_by_id(
    document_id: DocumentId,
    use_case: Annotated[GetDocumentStatus, Depends(get_document_status)],
) -> VerificationResponse:
    return _to_response(await use_case.execute(document_id))
