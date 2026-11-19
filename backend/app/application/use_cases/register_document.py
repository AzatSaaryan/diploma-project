from dataclasses import dataclass
from datetime import datetime
from typing import final

from app.application.ports.pdf_renderer import PdfRenderer
from app.application.ports.registry import Registry
from app.domain.document import new_document_id
from app.domain.fields import DocumentFields
from app.domain.hashing import hash_document_id, hash_fields


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    document_id: str
    transaction_hash: str
    pdf: bytes


@final
class RegisterDocument:
    def __init__(self, registry: Registry, renderer: PdfRenderer) -> None:
        self._registry = registry
        self._renderer = renderer

    async def execute(
        self, fields: DocumentFields, expires_at: datetime | None = None
    ) -> RegistrationResult:
        document_id = new_document_id()
        fields_hash = hash_fields(fields, document_id)
        pdf = self._renderer.render(fields, document_id)
        transaction_hash = await self._registry.register(
            hash_document_id(document_id), fields_hash, expires_at
        )
        return RegistrationResult(document_id, transaction_hash, pdf)
