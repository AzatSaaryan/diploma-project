from dataclasses import dataclass

import pytest

from app.adapters.outbound.in_memory_registry import InMemoryRegistry
from app.application.use_cases.lookup_document import LookupDocument
from app.application.use_cases.register_document import RegisterDocument
from app.application.use_cases.revoke_document import RevokeDocument
from app.application.use_cases.verify_document_fields import VerifyDocumentFields
from app.application.use_cases.verify_document_file import VerifyDocumentFile
from app.domain.fields import DocumentFields
from tests.fakes import FakePdfRenderer, FixedClock

ISSUER = "0xissuer"
BOB = DocumentFields("Bob", "Smith")


@dataclass
class Env:
    clock: FixedClock
    registry: InMemoryRegistry
    renderer: FakePdfRenderer
    register: RegisterDocument
    verify_file: VerifyDocumentFile
    lookup: LookupDocument
    verify_fields: VerifyDocumentFields
    revoke: RevokeDocument


@pytest.fixture
def env() -> Env:
    clock = FixedClock()
    registry = InMemoryRegistry(ISSUER, clock)
    renderer = FakePdfRenderer()
    return Env(
        clock=clock,
        registry=registry,
        renderer=renderer,
        register=RegisterDocument(registry, renderer),
        verify_file=VerifyDocumentFile(registry, renderer, clock),
        lookup=LookupDocument(registry),
        verify_fields=VerifyDocumentFields(registry, clock),
        revoke=RevokeDocument(registry),
    )
