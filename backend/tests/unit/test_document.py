import re

import pytest

from app.domain.document import ensure_pdf, new_document_id
from app.domain.errors import InvalidDocumentFile


def test_new_document_id_format() -> None:
    assert re.fullmatch(r"[0-9a-f]{32}", new_document_id())


def test_new_document_ids_are_unique() -> None:
    assert len({new_document_id() for _ in range(100)}) == 100


def test_ensure_pdf_accepts_pdf() -> None:
    ensure_pdf(b"%PDF-1.7\n...")


@pytest.mark.parametrize("data", [b"", b"hello", b" %PDF-1.7", b"PK\x03\x04"])
def test_ensure_pdf_rejects_non_pdf(data: bytes) -> None:
    with pytest.raises(InvalidDocumentFile):
        ensure_pdf(data)
