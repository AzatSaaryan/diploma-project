from datetime import UTC, datetime, timedelta

import pytest

from app.domain.document import DocumentRecord
from app.domain.hashing import compute_hash
from app.domain.status import Status
from app.domain.verification import decide_status

NOW = datetime(2026, 1, 1, tzinfo=UTC)
HASH = compute_hash(b"doc")
OTHER_HASH = compute_hash(b"other")


def make_record(
    *,
    revoked: bool = False,
    expires_at: datetime | None = None,
) -> DocumentRecord:
    return DocumentRecord(
        document_hash=HASH,
        issuer="0xissuer",
        issued_at=NOW - timedelta(days=1),
        expires_at=expires_at,
        revoked=revoked,
    )


def test_not_registered() -> None:
    status = decide_status(None, file_hash=HASH, issuer_authorized=True, now=NOW)
    assert status is Status.NOT_REGISTERED


def test_valid() -> None:
    status = decide_status(
        make_record(), file_hash=HASH, issuer_authorized=True, now=NOW
    )
    assert status is Status.VALID


def test_modified() -> None:
    status = decide_status(
        make_record(), file_hash=OTHER_HASH, issuer_authorized=True, now=NOW
    )
    assert status is Status.MODIFIED


def test_revoked() -> None:
    status = decide_status(
        make_record(revoked=True), file_hash=HASH, issuer_authorized=True, now=NOW
    )
    assert status is Status.REVOKED


def test_issuer_not_authorized() -> None:
    status = decide_status(
        make_record(), file_hash=HASH, issuer_authorized=False, now=NOW
    )
    assert status is Status.ISSUER_NOT_AUTHORIZED


def test_expired() -> None:
    record = make_record(expires_at=NOW - timedelta(seconds=1))
    status = decide_status(record, file_hash=HASH, issuer_authorized=True, now=NOW)
    assert status is Status.EXPIRED


def test_expiry_boundary_counts_as_expired() -> None:
    record = make_record(expires_at=NOW)
    status = decide_status(record, file_hash=HASH, issuer_authorized=True, now=NOW)
    assert status is Status.EXPIRED


def test_not_yet_expired_is_valid() -> None:
    record = make_record(expires_at=NOW + timedelta(seconds=1))
    status = decide_status(record, file_hash=HASH, issuer_authorized=True, now=NOW)
    assert status is Status.VALID


def test_verification_by_id_skips_modified_check() -> None:
    status = decide_status(
        make_record(), file_hash=None, issuer_authorized=True, now=NOW
    )
    assert status is Status.VALID


@pytest.mark.parametrize(
    ("file_hash", "revoked", "authorized", "expired", "expected"),
    [
        (OTHER_HASH, True, False, True, Status.MODIFIED),
        (HASH, True, False, True, Status.REVOKED),
        (HASH, False, False, True, Status.ISSUER_NOT_AUTHORIZED),
        (HASH, False, True, True, Status.EXPIRED),
        (HASH, False, True, False, Status.VALID),
        (None, True, True, False, Status.REVOKED),
    ],
)
def test_priority(
    file_hash: bytes | None,
    revoked: bool,
    authorized: bool,
    expired: bool,
    expected: Status,
) -> None:
    record = make_record(
        revoked=revoked,
        expires_at=NOW - timedelta(days=1) if expired else None,
    )
    status = decide_status(
        record, file_hash=file_hash, issuer_authorized=authorized, now=NOW
    )
    assert status is expected


def test_naive_datetime_is_rejected() -> None:
    record = make_record(expires_at=NOW + timedelta(days=1))
    with pytest.raises(TypeError):
        _ = decide_status(
            record,
            file_hash=HASH,
            issuer_authorized=True,
            now=datetime(2026, 1, 1),
        )
