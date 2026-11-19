import hashlib
import json

from app.domain.fields import DocumentFields


def compute_hash(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def hash_document_id(document_id: str) -> bytes:
    return compute_hash(document_id.encode())


def hash_fields(fields: DocumentFields, document_id: str) -> bytes:
    normalized = fields.normalized()
    payload = json.dumps(
        {
            "document_id": document_id,
            "first_name": normalized.first_name,
            "last_name": normalized.last_name,
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return compute_hash(payload.encode())
