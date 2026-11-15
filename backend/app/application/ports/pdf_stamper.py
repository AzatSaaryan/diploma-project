from typing import Protocol


class PdfStamper(Protocol):
    def stamp(self, pdf: bytes, document_id: str) -> bytes:
        """Return the PDF with a QR code and the document ID in its metadata."""
        ...

    def extract_id(self, pdf: bytes) -> str | None: ...
