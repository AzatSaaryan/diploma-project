from datetime import datetime
from typing import Protocol

from app.domain.document import DocumentRecord


class Registry(Protocol):
    async def register(
        self,
        id_hash: bytes,
        fields_hash: bytes,
        expires_at: datetime | None,
    ) -> str: ...

    async def get(self, id_hash: bytes) -> DocumentRecord | None: ...

    async def revoke(self, id_hash: bytes) -> str: ...

    async def is_issuer_authorized(self, issuer: str) -> bool: ...
