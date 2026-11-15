from io import BytesIO

import pytest
from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from app.adapters.outbound.pdf_stamper import PypdfStamper
from app.domain.errors import InvalidDocumentFile

DOC_ID = "ab" * 16


def make_pdf(pages: int = 1) -> bytes:
    buffer = BytesIO()
    canvas = Canvas(buffer)
    for number in range(pages):
        canvas.drawString(100, 700, f"Diploma page {number}")
        canvas.showPage()
    canvas.save()
    return buffer.getvalue()


@pytest.fixture
def stamper() -> PypdfStamper:
    return PypdfStamper("http://localhost:8000/")


def test_extract_id_roundtrip(stamper: PypdfStamper) -> None:
    stamped = stamper.stamp(make_pdf(), DOC_ID)

    assert stamper.extract_id(stamped) == DOC_ID


def test_result_is_still_a_pdf_with_qr_image(stamper: PypdfStamper) -> None:
    stamped = stamper.stamp(make_pdf(pages=2), DOC_ID)

    reader = PdfReader(BytesIO(stamped))
    assert stamped.startswith(b"%PDF-")
    assert len(reader.pages) == 2
    assert len(reader.pages[0].images) == 1
    assert len(reader.pages[1].images) == 0


def test_original_text_is_preserved(stamper: PypdfStamper) -> None:
    stamped = stamper.stamp(make_pdf(), DOC_ID)

    text = PdfReader(BytesIO(stamped)).pages[0].extract_text()
    assert "Diploma page 0" in text


def test_pdf_without_id_returns_none(stamper: PypdfStamper) -> None:
    assert stamper.extract_id(make_pdf()) is None


def test_garbage_returns_none(stamper: PypdfStamper) -> None:
    assert stamper.extract_id(b"%PDF-1.4 garbage") is None


def test_stamping_broken_pdf_raises(stamper: PypdfStamper) -> None:
    with pytest.raises(InvalidDocumentFile):
        _ = stamper.stamp(b"%PDF-1.4 garbage", DOC_ID)
