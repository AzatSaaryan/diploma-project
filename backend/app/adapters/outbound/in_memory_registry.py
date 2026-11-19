import secrets
from dataclasses import replace
from datetime import datetime
from typing import final

from app.application.ports.clock import Clock
from app.domain.document import DocumentRecord


@final
class InMemoryRegistry:
    def __init__(self, issuer: str, clock: Clock) -> None:
        self._issuer = issuer
        self._clock = clock
        self._records: dict[bytes, DocumentRecord] = {}
        self._authorized: set[str] = {issuer}

    async def register(
        self,
        id_hash: bytes,
        fields_hash: bytes,
        expires_at: datetime | None,
    ) -> str:
        if id_hash in self._records:
            raise ValueError("Document is already registered")
        self._records[id_hash] = DocumentRecord(
            fields_hash=fields_hash,
            issuer=self._issuer,
            issued_at=self._clock(),
            expires_at=expires_at,
            revoked=False,
        )
        return self._fake_tx_hash()

    async def get(self, id_hash: bytes) -> DocumentRecord | None:
        return self._records.get(id_hash)

    async def revoke(self, id_hash: bytes) -> str:
        record = self._records.get(id_hash)
        if record is None:
            raise KeyError("Document is not registered")
        self._records[id_hash] = replace(record, revoked=True)
        return self._fake_tx_hash()

    async def is_issuer_authorized(self, issuer: str) -> bool:
        return issuer in self._authorized

    def deauthorize(self, issuer: str) -> None:
        self._authorized.discard(issuer)

    @staticmethod
    def _fake_tx_hash() -> str:
        return "0x" + secrets.token_hex(32)
