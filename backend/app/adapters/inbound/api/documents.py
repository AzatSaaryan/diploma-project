from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.adapters.inbound.api.deps import (
    DocumentId,
    get_register_document,
    get_revoke_document,
    require_api_key,
)
from app.adapters.inbound.api.schemas import RegisterRequest, RevocationResponse
from app.application.use_cases.register_document import RegisterDocument
from app.application.use_cases.revoke_document import RevokeDocument

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(require_api_key)],
)


@router.post(
    "",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def register_document(
    body: RegisterRequest,
    use_case: Annotated[RegisterDocument, Depends(get_register_document)],
) -> Response:
    result = await use_case.execute(body.to_domain(), body.expires_at)
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
    _ = await use_case.execute(document_id)
    return RevocationResponse(document_id=document_id, revoked=True)
