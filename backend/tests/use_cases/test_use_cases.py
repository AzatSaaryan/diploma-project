from datetime import timedelta

import pytest

from app.application.errors import RegistryUnavailable
from app.application.use_cases.lookup_document import LookupDocument
from app.application.use_cases.register_document import RegisterDocument
from app.application.use_cases.revoke_document import RevokeDocument
from app.application.use_cases.verify_document_fields import VerifyDocumentFields
from app.application.use_cases.verify_document_file import VerifyDocumentFile
from app.domain.errors import (
    DocumentFieldsUnreadable,
    DocumentNotFound,
    InvalidDocumentFields,
    InvalidDocumentFile,
)
from app.domain.fields import DocumentFields
from app.domain.status import Status
from tests.fakes import FailingRegistry, FakePdfRenderer, FixedClock, fake_pdf
from tests.use_cases.conftest import BOB, Env

UNKNOWN_ID = "0" * 32


async def test_register_returns_id_tx_and_pdf(env: Env) -> None:
    registered = await env.register.execute(BOB)

    assert len(registered.document_id) == 32
    assert registered.transaction_hash.startswith("0x")
    assert env.renderer.read_document_id(registered.pdf) == registered.document_id


async def test_register_rejects_empty_fields(env: Env) -> None:
    with pytest.raises(InvalidDocumentFields):
        _ = await env.register.execute(DocumentFields(" ", "Smith"))


# Path 1: PDF file


async def test_file_same_pdf_is_valid(env: Env) -> None:
    registered = await env.register.execute(BOB)

    result = await env.verify_file.execute(registered.pdf)

    assert result.status is Status.VALID
    assert result.document_id == registered.document_id
    assert result.fields == BOB


async def test_file_with_changed_name_is_modified(env: Env) -> None:
    registered = await env.register.execute(BOB)
    forged = fake_pdf(registered.document_id, "Alice", "Smith")

    result = await env.verify_file.execute(forged)

    assert result.status is Status.MODIFIED
    assert result.fields == DocumentFields("Alice", "Smith")


async def test_file_without_id_is_not_registered(env: Env) -> None:
    result = await env.verify_file.execute(fake_pdf(None, "Bob", "Smith"))

    assert result.status is Status.NOT_REGISTERED
    assert result.document_id is None


async def test_file_with_unknown_id_is_not_registered(env: Env) -> None:
    result = await env.verify_file.execute(fake_pdf(UNKNOWN_ID, "Bob", "Smith"))

    assert result.status is Status.NOT_REGISTERED
    assert result.document_id == UNKNOWN_ID


async def test_file_with_unreadable_fields_raises(env: Env) -> None:
    registered = await env.register.execute(BOB)
    broken = f"%PDF-fake\nID:{registered.document_id}\n".encode()

    with pytest.raises(DocumentFieldsUnreadable):
        _ = await env.verify_file.execute(broken)


async def test_file_must_be_pdf(env: Env) -> None:
    with pytest.raises(InvalidDocumentFile):
        _ = await env.verify_file.execute(b"not a pdf")


# Path 2: paper diploma, QR -> lookup -> manual fields


async def test_lookup(env: Env) -> None:
    registered = await env.register.execute(BOB)

    assert (await env.lookup.execute(registered.document_id)).registered
    assert not (await env.lookup.execute(UNKNOWN_ID)).registered


async def test_manual_fields_valid(env: Env) -> None:
    registered = await env.register.execute(BOB)

    result = await env.verify_fields.execute(
        registered.document_id, DocumentFields("  bob ", "SMITH")
    )

    assert result.status is Status.VALID


async def test_manual_wrong_name_is_modified(env: Env) -> None:
    registered = await env.register.execute(BOB)

    result = await env.verify_fields.execute(
        registered.document_id, DocumentFields("Alice", "Smith")
    )

    assert result.status is Status.MODIFIED


async def test_manual_unknown_id_is_not_registered(env: Env) -> None:
    result = await env.verify_fields.execute(UNKNOWN_ID, BOB)

    assert result.status is Status.NOT_REGISTERED


async def test_manual_empty_fields_are_rejected(env: Env) -> None:
    registered = await env.register.execute(BOB)

    with pytest.raises(InvalidDocumentFields):
        _ = await env.verify_fields.execute(
            registered.document_id, DocumentFields("", "Smith")
        )


# Registry state


async def test_revoked(env: Env) -> None:
    registered = await env.register.execute(BOB)
    _ = await env.revoke.execute(registered.document_id)

    by_file = await env.verify_file.execute(registered.pdf)
    by_fields = await env.verify_fields.execute(registered.document_id, BOB)

    assert by_file.status is Status.REVOKED
    assert by_fields.status is Status.REVOKED


async def test_modified_wins_over_revoked(env: Env) -> None:
    registered = await env.register.execute(BOB)
    _ = await env.revoke.execute(registered.document_id)

    result = await env.verify_fields.execute(
        registered.document_id, DocumentFields("Alice", "Smith")
    )

    assert result.status is Status.MODIFIED


async def test_revoke_twice_writes_once(env: Env) -> None:
    registered = await env.register.execute(BOB)

    first = await env.revoke.execute(registered.document_id)
    second = await env.revoke.execute(registered.document_id)

    assert first.transaction_hash is not None
    assert second.transaction_hash is None


async def test_revoke_unknown_raises(env: Env) -> None:
    with pytest.raises(DocumentNotFound):
        _ = await env.revoke.execute(UNKNOWN_ID)


async def test_expired_after_deadline(env: Env) -> None:
    registered = await env.register.execute(
        BOB, expires_at=env.clock.now + timedelta(days=1)
    )
    assert (await env.verify_file.execute(registered.pdf)).status is Status.VALID

    env.clock.now += timedelta(days=1)

    assert (await env.verify_file.execute(registered.pdf)).status is Status.EXPIRED


async def test_deauthorized_issuer(env: Env) -> None:
    registered = await env.register.execute(BOB)
    env.registry.deauthorize("0xissuer")

    result = await env.verify_fields.execute(registered.document_id, BOB)

    assert result.status is Status.ISSUER_NOT_AUTHORIZED


async def test_registry_failure_propagates() -> None:
    registry = FailingRegistry()
    renderer = FakePdfRenderer()
    clock = FixedClock()
    pdf = fake_pdf(UNKNOWN_ID, "Bob", "Smith")

    with pytest.raises(RegistryUnavailable):
        _ = await RegisterDocument(registry, renderer).execute(BOB)
    with pytest.raises(RegistryUnavailable):
        _ = await VerifyDocumentFile(registry, renderer, clock).execute(pdf)
    with pytest.raises(RegistryUnavailable):
        _ = await LookupDocument(registry).execute(UNKNOWN_ID)
    with pytest.raises(RegistryUnavailable):
        _ = await VerifyDocumentFields(registry, clock).execute(UNKNOWN_ID, BOB)
    with pytest.raises(RegistryUnavailable):
        _ = await RevokeDocument(registry).execute(UNKNOWN_ID)
