from dataclasses import dataclass
from datetime import datetime
from typing import final

from app.application.ports.pdf_stamper import PdfStamper
from app.application.ports.registry import Registry
from app.domain.document import ensure_pdf, new_document_id
from app.domain.hashing import compute_hash


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    document_id: str
    transaction_hash: str
    pdf: bytes


@final
class RegisterDocument:
    def __init__(self, registry: Registry, stamper: PdfStamper) -> None:
        self._registry = registry
        self._stamper = stamper

    async def execute(
        self, pdf: bytes, expires_at: datetime | None = None
    ) -> RegistrationResult:
        ensure_pdf(pdf)
        document_id = new_document_id()
        stamped = self._stamper.stamp(pdf, document_id)
        transaction_hash = await self._registry.register(
            document_id, compute_hash(stamped), expires_at
        )
        return RegistrationResult(document_id, transaction_hash, stamped)
