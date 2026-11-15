from typing import final

from app.application.ports.clock import Clock
from app.application.ports.registry import Registry
from app.application.use_cases.resolve_status import (
    VerificationResult,
    resolve_status,
)


@final
class GetDocumentStatus:
    def __init__(self, registry: Registry, clock: Clock) -> None:
        self._registry = registry
        self._clock = clock

    async def execute(self, document_id: str) -> VerificationResult:
        return await resolve_status(self._registry, self._clock, document_id, None)
