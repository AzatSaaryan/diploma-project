from typing import final

from app.application.ports.clock import Clock
from app.application.ports.pdf_stamper import PdfStamper
from app.application.ports.registry import Registry
from app.application.use_cases.resolve_status import (
    VerificationResult,
    resolve_status,
)
from app.domain.document import ensure_pdf
from app.domain.hashing import compute_hash


@final
class VerifyDocument:
    def __init__(self, registry: Registry, stamper: PdfStamper, clock: Clock) -> None:
        self._registry = registry
        self._stamper = stamper
        self._clock = clock

    async def execute(self, pdf: bytes) -> VerificationResult:
        ensure_pdf(pdf)
        document_id = self._stamper.extract_id(pdf)
        return await resolve_status(
            self._registry, self._clock, document_id, compute_hash(pdf)
        )
