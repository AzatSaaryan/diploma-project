from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Path, UploadFile, status
from fastapi.responses import Response

from app.adapters.inbound.api.deps import (
    SettingsDep,
    get_register_document,
    get_revoke_document,
    read_upload,
    require_api_key,
)
from app.adapters.inbound.api.schemas import RevocationResponse
from app.application.use_cases.register_document import RegisterDocument
from app.application.use_cases.revoke_document import RevokeDocument

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(require_api_key)],
)

DocumentId = Annotated[str, Path(pattern=r"^[0-9a-f]{32}$")]


@router.post(
    "",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def register_document(
    file: UploadFile,
    settings: SettingsDep,
    use_case: Annotated[RegisterDocument, Depends(get_register_document)],
    expires_at: Annotated[datetime | None, Form()] = None,
) -> Response:
    if expires_at is not None and expires_at.tzinfo is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "expires_at must include a timezone offset",
        )
    result = await use_case.execute(await read_upload(file, settings), expires_at)
    return Response(
        content=result.pdf,
        media_type="application/pdf",
        headers={
            "X-Document-Id": result.document_id,
            "X-Transaction-Hash": result.transaction_hash,
            "Content-Disposition": f'attachment; filename="{result.document_id}.pdf"',
        },
    )


@router.post("/{document_id}/revoke")
async def revoke_document(
    document_id: DocumentId,
    use_case: Annotated[RevokeDocument, Depends(get_revoke_document)],
) -> RevocationResponse:
    result = await use_case.execute(document_id)
    return RevocationResponse(
        document_id=document_id, transaction_hash=result.transaction_hash
    )
