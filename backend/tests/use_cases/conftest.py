from dataclasses import dataclass

import pytest

from app.adapters.outbound.in_memory_registry import InMemoryRegistry
from app.application.use_cases.get_document_status import GetDocumentStatus
from app.application.use_cases.register_document import RegisterDocument
from app.application.use_cases.revoke_document import RevokeDocument
from app.application.use_cases.verify_document import VerifyDocument
from tests.fakes import FakePdfStamper, FixedClock

ISSUER = "0xissuer"
PDF = b"%PDF-1.7\nhello"


@dataclass
class Env:
    clock: FixedClock
    registry: InMemoryRegistry
    stamper: FakePdfStamper
    register: RegisterDocument
    verify: VerifyDocument
    get_status: GetDocumentStatus
    revoke: RevokeDocument


@pytest.fixture
def env() -> Env:
    clock = FixedClock()
    registry = InMemoryRegistry(ISSUER, clock)
    stamper = FakePdfStamper()
    return Env(
        clock=clock,
        registry=registry,
        stamper=stamper,
        register=RegisterDocument(registry, stamper),
        verify=VerifyDocument(registry, stamper, clock),
        get_status=GetDocumentStatus(registry, clock),
        revoke=RevokeDocument(registry),
    )
