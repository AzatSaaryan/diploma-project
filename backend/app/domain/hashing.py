import hashlib


def compute_hash(data: bytes) -> bytes:
    """SHA-256 digest of the document bytes (32 bytes)."""
    return hashlib.sha256(data).digest()
