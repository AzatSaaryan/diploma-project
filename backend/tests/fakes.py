# pyright: reportUnusedParameter=false
from datetime import UTC, datetime
from typing import final

from app.application.errors import RegistryUnavailable
from app.domain.document import DocumentRecord
from app.domain.errors import DocumentFieldsUnreadable
from app.domain.fields import DocumentFields

FIXED_NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def fake_pdf(document_id: str | None, first_name: str, last_name: str) -> bytes:
    lines = ["%PDF-fake"]
    if document_id is not None:
        lines.append(f"ID:{document_id}")
    lines += [f"FIRST:{first_name}", f"LAST:{last_name}"]
    return "\n".join(lines).encode()


def _value(pdf: bytes, prefix: str) -> str | None:
    for line in pdf.decode().splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix)
    return None


@final
class FakePdfRenderer:
    def render(self, fields: DocumentFields, document_id: str) -> bytes:
        return fake_pdf(document_id, fields.first_name, fields.last_name)

    def read_document_id(self, pdf: bytes) -> str | None:
        return _value(pdf, "ID:")

    def read_fields(self, pdf: bytes) -> DocumentFields:
        first_name = _value(pdf, "FIRST:")
        last_name = _value(pdf, "LAST:")
        if first_name is None or last_name is None:
            raise DocumentFieldsUnreadable("fake: fields not found")
        return DocumentFields(first_name, last_name)


@final
class FailingRegistry:
    async def register(
        self,
        id_hash: bytes,
        fields_hash: bytes,
        expires_at: datetime | None,
    ) -> str:
        raise RegistryUnavailable

    async def get(self, id_hash: bytes) -> DocumentRecord | None:
        raise RegistryUnavailable

    async def revoke(self, id_hash: bytes) -> str:
        raise RegistryUnavailable

    async def is_issuer_authorized(self, issuer: str) -> bool:
        raise RegistryUnavailable


@final
class FixedClock:
    now: datetime

    def __init__(self, now: datetime = FIXED_NOW) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now
