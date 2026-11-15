from dataclasses import dataclass

from app.application.ports.clock import Clock
from app.application.ports.registry import Registry
from app.domain.document import DocumentRecord
from app.domain.status import Status
from app.domain.verification import decide_status


@dataclass(frozen=True, slots=True)
class VerificationResult:
    status: Status
    document_id: str | None
    record: DocumentRecord | None


async def resolve_status(
    registry: Registry,
    clock: Clock,
    document_id: str | None,
    file_hash: bytes | None,
) -> VerificationResult:
    """Shared by verification by file and by ID."""
    if document_id is None:
        return VerificationResult(Status.NOT_REGISTERED, None, None)
    record = await registry.get(document_id)
    if record is None:
        return VerificationResult(Status.NOT_REGISTERED, document_id, None)
    authorized = await registry.is_issuer_authorized(record.issuer)
    status = decide_status(
        record, file_hash=file_hash, issuer_authorized=authorized, now=clock()
    )
    return VerificationResult(status, document_id, record)
