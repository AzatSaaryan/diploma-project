from typing import final

from app.application.ports.clock import Clock
from app.application.ports.registry import Registry
from app.application.use_cases.evaluate import (
    VerificationResult,
    evaluate,
    not_registered,
)
from app.domain.fields import DocumentFields
from app.domain.hashing import hash_document_id


@final
class VerifyDocumentFields:
    def __init__(self, registry: Registry, clock: Clock) -> None:
        self._registry = registry
        self._clock = clock

    async def execute(
        self, document_id: str, fields: DocumentFields
    ) -> VerificationResult:
        _ = fields.normalized()
        record = await self._registry.get(hash_document_id(document_id))
        if record is None:
            return not_registered(document_id)
        return await evaluate(self._registry, self._clock, document_id, record, fields)
