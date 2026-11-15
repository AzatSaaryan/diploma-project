from datetime import timedelta

import pytest

from app.application.errors import RegistryUnavailable
from app.application.use_cases.get_document_status import GetDocumentStatus
from app.application.use_cases.register_document import RegisterDocument
from app.application.use_cases.revoke_document import RevokeDocument
from app.application.use_cases.verify_document import VerifyDocument
from app.domain.errors import DocumentNotFound, InvalidDocumentFile
from app.domain.status import Status
from tests.fakes import FailingRegistry, FakePdfStamper, FixedClock
from tests.use_cases.conftest import PDF, Env


async def test_register_then_verify_same_file_is_valid(env: Env) -> None:
    registered = await env.register.execute(PDF)

    result = await env.verify.execute(registered.pdf)

    assert result.status is Status.VALID
    assert result.document_id == registered.document_id
    assert registered.transaction_hash.startswith("0x")


async def test_one_changed_byte_is_modified(env: Env) -> None:
    registered = await env.register.execute(PDF)
    tampered = bytearray(registered.pdf)
    tampered[8] ^= 0x01

    result = await env.verify.execute(bytes(tampered))

    assert result.status is Status.MODIFIED


async def test_other_file_with_same_id_is_modified(env: Env) -> None:
    registered = await env.register.execute(PDF)
    forged = env.stamper.stamp(b"%PDF-1.7\nforged", registered.document_id)

    result = await env.verify.execute(forged)

    assert result.status is Status.MODIFIED


async def test_file_without_id_is_not_registered(env: Env) -> None:
    result = await env.verify.execute(PDF)

    assert result.status is Status.NOT_REGISTERED
    assert result.document_id is None


async def test_unknown_id_is_not_registered(env: Env) -> None:
    result = await env.get_status.execute("0" * 32)

    assert result.status is Status.NOT_REGISTERED
    assert result.document_id == "0" * 32


async def test_revoked(env: Env) -> None:
    registered = await env.register.execute(PDF)
    _ = await env.revoke.execute(registered.document_id)

    by_file = await env.verify.execute(registered.pdf)
    by_id = await env.get_status.execute(registered.document_id)

    assert by_file.status is Status.REVOKED
    assert by_id.status is Status.REVOKED


async def test_revoke_twice_writes_once(env: Env) -> None:
    registered = await env.register.execute(PDF)

    first = await env.revoke.execute(registered.document_id)
    second = await env.revoke.execute(registered.document_id)

    assert first.transaction_hash is not None
    assert second.transaction_hash is None


async def test_revoke_unknown_raises(env: Env) -> None:
    with pytest.raises(DocumentNotFound):
        _ = await env.revoke.execute("0" * 32)


async def test_expired_after_deadline(env: Env) -> None:
    registered = await env.register.execute(
        PDF, expires_at=env.clock.now + timedelta(days=1)
    )
    assert (await env.verify.execute(registered.pdf)).status is Status.VALID

    env.clock.now += timedelta(days=1)

    assert (await env.verify.execute(registered.pdf)).status is Status.EXPIRED


async def test_deauthorized_issuer(env: Env) -> None:
    registered = await env.register.execute(PDF)
    env.registry.deauthorize("0xissuer")

    result = await env.verify.execute(registered.pdf)

    assert result.status is Status.ISSUER_NOT_AUTHORIZED


async def test_register_rejects_non_pdf(env: Env) -> None:
    with pytest.raises(InvalidDocumentFile):
        _ = await env.register.execute(b"not a pdf")


async def test_verify_rejects_non_pdf(env: Env) -> None:
    with pytest.raises(InvalidDocumentFile):
        _ = await env.verify.execute(b"not a pdf")


async def test_registry_failure_propagates() -> None:
    registry = FailingRegistry()
    stamper = FakePdfStamper()
    clock = FixedClock()
    stamped = stamper.stamp(PDF, "a" * 32)

    with pytest.raises(RegistryUnavailable):
        _ = await RegisterDocument(registry, stamper).execute(PDF)
    with pytest.raises(RegistryUnavailable):
        _ = await VerifyDocument(registry, stamper, clock).execute(stamped)
    with pytest.raises(RegistryUnavailable):
        _ = await GetDocumentStatus(registry, clock).execute("a" * 32)
    with pytest.raises(RegistryUnavailable):
        _ = await RevokeDocument(registry).execute("a" * 32)
