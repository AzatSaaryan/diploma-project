from io import BytesIO

import pytest
from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from app.adapters.outbound.pdf_renderer import ReportlabPdfRenderer
from app.domain.errors import DocumentFieldsUnreadable
from app.domain.fields import DocumentFields

DOC_ID = "ab" * 16
BOB = DocumentFields("Bob", "Smith")


def plain_pdf(*lines: str) -> bytes:
    buffer = BytesIO()
    canvas = Canvas(buffer)
    for number, line in enumerate(lines):
        canvas.drawString(100, 700 - 20 * number, line)
    canvas.showPage()
    canvas.save()
    return buffer.getvalue()


@pytest.fixture
def renderer() -> ReportlabPdfRenderer:
    return ReportlabPdfRenderer("http://localhost:8000/")


def test_roundtrip(renderer: ReportlabPdfRenderer) -> None:
    pdf = renderer.render(BOB, DOC_ID)

    assert pdf.startswith(b"%PDF-")
    assert renderer.read_document_id(pdf) == DOC_ID
    assert renderer.read_fields(pdf) == BOB


@pytest.mark.parametrize(
    "fields",
    [
        DocumentFields("Mary Ann", "O'Neil-Smith Jr."),
        DocumentFields("A" * 64, "B" * 64),
    ],
)
def test_roundtrip_special_and_long_names(
    renderer: ReportlabPdfRenderer, fields: DocumentFields
) -> None:
    assert renderer.read_fields(renderer.render(fields, DOC_ID)) == fields


def test_pdf_has_one_page_with_qr(renderer: ReportlabPdfRenderer) -> None:
    reader = PdfReader(BytesIO(renderer.render(BOB, DOC_ID)))

    assert len(reader.pages) == 1
    assert len(reader.pages[0].images) == 1


def test_verification_url(renderer: ReportlabPdfRenderer) -> None:
    assert renderer.verification_url(DOC_ID) == (
        f"http://localhost:8000/verifications/{DOC_ID}"
    )


def test_pdf_without_id_returns_none(renderer: ReportlabPdfRenderer) -> None:
    assert renderer.read_document_id(plain_pdf("hello")) is None


def test_garbage_id_returns_none(renderer: ReportlabPdfRenderer) -> None:
    assert renderer.read_document_id(b"%PDF-1.4 garbage") is None


def test_foreign_template_is_unreadable(renderer: ReportlabPdfRenderer) -> None:
    with pytest.raises(DocumentFieldsUnreadable):
        _ = renderer.read_fields(plain_pdf("Name: Bob Smith"))


def test_duplicated_label_is_unreadable(renderer: ReportlabPdfRenderer) -> None:
    pdf = plain_pdf("First name: Bob", "First name: Alice", "Last name: Smith")

    with pytest.raises(DocumentFieldsUnreadable):
        _ = renderer.read_fields(pdf)


def test_garbage_fields_are_unreadable(renderer: ReportlabPdfRenderer) -> None:
    with pytest.raises(DocumentFieldsUnreadable):
        _ = renderer.read_fields(b"%PDF-1.4 garbage")
