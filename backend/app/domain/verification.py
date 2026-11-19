from datetime import datetime

from app.domain.document import DocumentRecord
from app.domain.status import Status


def decide_status(
    record: DocumentRecord | None,
    *,
    fields_hash: bytes,
    issuer_authorized: bool,
    now: datetime,
) -> Status:
    if record is None:
        return Status.NOT_REGISTERED
    if fields_hash != record.fields_hash:
        return Status.MODIFIED
    if record.revoked:
        return Status.REVOKED
    if not issuer_authorized:
        return Status.ISSUER_NOT_AUTHORIZED
    if record.expires_at is not None and now >= record.expires_at:
        return Status.EXPIRED
    return Status.VALID
