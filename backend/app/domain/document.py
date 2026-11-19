import secrets
from dataclasses import dataclass
from datetime import datetime

from app.domain.errors import InvalidDocumentFile

PDF_SIGNATURE = b"%PDF-"
DOCUMENT_ID_PATTERN = r"^[0-9a-f]{32}$"


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    fields_hash: bytes
    issuer: str
    issued_at: datetime
    expires_at: datetime | None
    revoked: bool


def new_document_id() -> str:
    return secrets.token_hex(16)


def ensure_pdf(data: bytes) -> None:
    if not data.startswith(PDF_SIGNATURE):
        raise InvalidDocumentFile("File does not start with the %PDF- signature")
