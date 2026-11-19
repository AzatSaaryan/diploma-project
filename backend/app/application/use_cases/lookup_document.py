from dataclasses import dataclass
from typing import final

from app.application.ports.registry import Registry
from app.domain.hashing import hash_document_id


@dataclass(frozen=True, slots=True)
class LookupResult:
    document_id: str
    registered: bool


@final
class LookupDocument:
    def __init__(self, registry: Registry) -> None:
        self._registry = registry

    async def execute(self, document_id: str) -> LookupResult:
        record = await self._registry.get(hash_document_id(document_id))
        return LookupResult(document_id, record is not None)
