from typing import Protocol

from app.domain.fields import DocumentFields


class PdfRenderer(Protocol):
    def render(self, fields: DocumentFields, document_id: str) -> bytes: ...

    def read_document_id(self, pdf: bytes) -> str | None: ...

    def read_fields(self, pdf: bytes) -> DocumentFields: ...
