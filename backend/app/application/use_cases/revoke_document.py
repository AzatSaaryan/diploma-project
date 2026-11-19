from dataclasses import dataclass
from typing import final

from app.application.ports.registry import Registry
from app.domain.errors import DocumentNotFound
from app.domain.hashing import hash_document_id


@dataclass(frozen=True, slots=True)
class RevocationResult:
    transaction_hash: str | None


@final
class RevokeDocument:
    def __init__(self, registry: Registry) -> None:
        self._registry = registry

    async def execute(self, document_id: str) -> RevocationResult:
        id_hash = hash_document_id(document_id)
        record = await self._registry.get(id_hash)
        if record is None:
            raise DocumentNotFound(document_id)
        if record.revoked:
            return RevocationResult(None)
        return RevocationResult(await self._registry.revoke(id_hash))
