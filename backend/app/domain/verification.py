from datetime import datetime

from app.domain.document import DocumentRecord
from app.domain.status import Status


def decide_status(
    record: DocumentRecord | None,
    *,
    file_hash: bytes | None,
    issuer_authorized: bool,
    now: datetime,
) -> Status:
    """Priority: NOT_REGISTERED > MODIFIED > REVOKED > ISSUER_NOT_AUTHORIZED
    > EXPIRED > VALID. ``file_hash=None`` means verification by ID only, so the
    MODIFIED check is skipped. All datetimes must be timezone-aware.
    """
    if record is None:
        return Status.NOT_REGISTERED
    if file_hash is not None and file_hash != record.document_hash:
        return Status.MODIFIED
    if record.revoked:
        return Status.REVOKED
    if not issuer_authorized:
        return Status.ISSUER_NOT_AUTHORIZED
    if record.expires_at is not None and now >= record.expires_at:
        return Status.EXPIRED
    return Status.VALID
