from datetime import datetime
from typing import Protocol

from app.domain.document import DocumentRecord


class Registry(Protocol):
    async def register(
        self,
        document_id: str,
        document_hash: bytes,
        expires_at: datetime | None,
    ) -> str:
        """Store the document; returns the transaction hash."""
        ...

    async def get(self, document_id: str) -> DocumentRecord | None: ...

    async def revoke(self, document_id: str) -> str:
        """Mark the document as revoked; returns the transaction hash."""
        ...

    async def is_issuer_authorized(self, issuer: str) -> bool: ...
