from dataclasses import dataclass

from app.application.ports.clock import Clock
from app.application.ports.registry import Registry
from app.domain.document import DocumentRecord
from app.domain.fields import DocumentFields
from app.domain.hashing import hash_fields
from app.domain.status import Status
from app.domain.verification import decide_status


@dataclass(frozen=True, slots=True)
class VerificationResult:
    status: Status
    document_id: str | None
    fields: DocumentFields | None
    record: DocumentRecord | None


def not_registered(document_id: str | None) -> VerificationResult:
    return VerificationResult(Status.NOT_REGISTERED, document_id, None, None)


async def evaluate(
    registry: Registry,
    clock: Clock,
    document_id: str,
    record: DocumentRecord,
    fields: DocumentFields,
) -> VerificationResult:
    authorized = await registry.is_issuer_authorized(record.issuer)
    status = decide_status(
        record,
        fields_hash=hash_fields(fields, document_id),
        issuer_authorized=authorized,
        now=clock(),
    )
    return VerificationResult(status, document_id, fields, record)
