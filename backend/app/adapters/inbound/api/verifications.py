from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile

from app.adapters.inbound.api.deps import (
    DocumentId,
    SettingsDep,
    get_lookup_document,
    get_verify_document_fields,
    get_verify_document_file,
    read_upload,
)
from app.adapters.inbound.api.schemas import (
    FieldsIn,
    LookupResponse,
    VerificationResponse,
)
from app.application.use_cases.lookup_document import LookupDocument
from app.application.use_cases.verify_document_fields import VerifyDocumentFields
from app.application.use_cases.verify_document_file import VerifyDocumentFile

router = APIRouter(prefix="/verifications", tags=["verifications"])


@router.post("")
async def verify_file(
    file: UploadFile,
    settings: SettingsDep,
    use_case: Annotated[VerifyDocumentFile, Depends(get_verify_document_file)],
) -> VerificationResponse:
    result = await use_case.execute(await read_upload(file, settings))
    return VerificationResponse.from_result(result)


@router.post("/{document_id}/lookup")
async def lookup_document(
    document_id: DocumentId,
    use_case: Annotated[LookupDocument, Depends(get_lookup_document)],
) -> LookupResponse:
    result = await use_case.execute(document_id)
    return LookupResponse(document_id=result.document_id, registered=result.registered)


@router.post("/{document_id}")
async def verify_fields(
    document_id: DocumentId,
    body: FieldsIn,
    use_case: Annotated[VerifyDocumentFields, Depends(get_verify_document_fields)],
) -> VerificationResponse:
    result = await use_case.execute(document_id, body.to_domain())
    return VerificationResponse.from_result(result)
