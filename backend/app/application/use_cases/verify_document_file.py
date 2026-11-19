from typing import final

from app.application.ports.clock import Clock
from app.application.ports.pdf_renderer import PdfRenderer
from app.application.ports.registry import Registry
from app.application.use_cases.evaluate import (
    VerificationResult,
    evaluate,
    not_registered,
)
from app.domain.document import ensure_pdf
from app.domain.hashing import hash_document_id


@final
class VerifyDocumentFile:
    def __init__(self, registry: Registry, renderer: PdfRenderer, clock: Clock) -> None:
        self._registry = registry
        self._renderer = renderer
        self._clock = clock

    async def execute(self, pdf: bytes) -> VerificationResult:
        ensure_pdf(pdf)
        document_id = self._renderer.read_document_id(pdf)
        if document_id is None:
            return not_registered(None)
        record = await self._registry.get(hash_document_id(document_id))
        if record is None:
            return not_registered(document_id)
        fields = self._renderer.read_fields(pdf)
        return await evaluate(self._registry, self._clock, document_id, record, fields)
