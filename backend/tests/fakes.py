# pyright: reportUnusedParameter=false
from datetime import UTC, datetime
from typing import final

from app.application.errors import RegistryUnavailable
from app.domain.document import DocumentRecord

ID_MARKER = b"\n%%DOC-ID:"
FIXED_NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


@final
class FakePdfStamper:
    """Appends ``%%DOC-ID:<id>`` to the bytes; no real PDF handling."""

    def stamp(self, pdf: bytes, document_id: str) -> bytes:
        return pdf + ID_MARKER + document_id.encode()

    def extract_id(self, pdf: bytes) -> str | None:
        _, marker, tail = pdf.rpartition(ID_MARKER)
        if not marker:
            return None
        return tail.decode()


@final
class FailingRegistry:
    async def register(
        self,
        document_id: str,
        document_hash: bytes,
        expires_at: datetime | None,
    ) -> str:
        raise RegistryUnavailable

    async def get(self, document_id: str) -> DocumentRecord | None:
        raise RegistryUnavailable

    async def revoke(self, document_id: str) -> str:
        raise RegistryUnavailable

    async def is_issuer_authorized(self, issuer: str) -> bool:
        raise RegistryUnavailable


@final
class FixedClock:
    def __init__(self, now: datetime = FIXED_NOW) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now
