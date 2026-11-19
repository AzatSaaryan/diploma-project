import secrets
from dataclasses import replace
from datetime import datetime
from typing import final

from app.application.ports.clock import Clock
from app.domain.document import DocumentRecord
from app.domain.errors import DocumentNotFound


@final
class InMemoryRegistry:
    def __init__(self, issuer: str, clock: Clock) -> None:
        self._issuer = issuer
        self._clock = clock
        self._records: dict[str, DocumentRecord] = {}
        self._authorized: set[str] = {issuer}

    async def register(
        self,
        document_id: str,
        document_hash: bytes,
        expires_at: datetime | None,
    ) -> str:
        if document_id in self._records:
            raise ValueError(f"Document {document_id} is already registered")
        self._records[document_id] = DocumentRecord(
            document_hash=document_hash,
            issuer=self._issuer,
            issued_at=self._clock(),
            expires_at=expires_at,
            revoked=False,
        )
        return self._fake_tx_hash()

    async def get(self, document_id: str) -> DocumentRecord | None:
        return self._records.get(document_id)

    async def revoke(self, document_id: str) -> str:
        record = self._records.get(document_id)
        if record is None:
            raise DocumentNotFound(document_id)
        self._records[document_id] = replace(record, revoked=True)
        return self._fake_tx_hash()

    async def is_issuer_authorized(self, issuer: str) -> bool:
        return issuer in self._authorized

    def deauthorize(self, issuer: str) -> None:
        self._authorized.discard(issuer)

    @staticmethod
    def _fake_tx_hash() -> str:
        return "0x" + secrets.token_hex(32)
