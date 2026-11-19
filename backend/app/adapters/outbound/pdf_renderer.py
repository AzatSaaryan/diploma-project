# pyright: reportAny=false, reportUnknownMemberType=false
import re
from io import BytesIO
from typing import final

import qrcode
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PyPdfError
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from app.domain.errors import DocumentFieldsUnreadable
from app.domain.fields import DocumentFields

ID_METADATA_KEY = "/DocumentId"
FIRST_NAME_LABEL = "First name"
LAST_NAME_LABEL = "Last name"
FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
MARGIN = 72.0
FIELD_FONT_SIZE = 16.0
MIN_FONT_SIZE = 6.0
QR_SIZE = 110.0


@final
class ReportlabPdfRenderer:
    def __init__(self, public_base_url: str) -> None:
        self._base_url = public_base_url.rstrip("/")

    def render(self, fields: DocumentFields, document_id: str) -> bytes:
        width, height = A4
        buffer = BytesIO()
        canvas = Canvas(buffer, pagesize=A4)

        canvas.setFont(FONT_BOLD, 28)
        canvas.drawCentredString(width / 2, height - 2 * MARGIN, "DIPLOMA")

        y = height - 3.5 * MARGIN
        for label, value in (
            (FIRST_NAME_LABEL, fields.first_name),
            (LAST_NAME_LABEL, fields.last_name),
        ):
            line = f"{label}: {' '.join(value.split())}"
            canvas.setFont(FONT, self._fit_font_size(line, width - 2 * MARGIN))
            canvas.drawString(MARGIN, y, line)
            y -= 2 * FIELD_FONT_SIZE

        qr = qrcode.make(self.verification_url(document_id)).get_image()
        _ = canvas.drawImage(
            ImageReader(qr), width - MARGIN - QR_SIZE, MARGIN, QR_SIZE, QR_SIZE
        )
        canvas.showPage()
        canvas.save()
        return self._with_metadata(buffer.getvalue(), document_id)

    def verification_url(self, document_id: str) -> str:
        return f"{self._base_url}/verifications/{document_id}"

    def read_document_id(self, pdf: bytes) -> str | None:
        try:
            metadata = PdfReader(BytesIO(pdf)).metadata
        except PyPdfError:
            return None
        if metadata is None:
            return None
        value = metadata.get(ID_METADATA_KEY)
        return str(value) if value is not None else None

    def read_fields(self, pdf: bytes) -> DocumentFields:
        try:
            reader = PdfReader(BytesIO(pdf))
            text = "\n".join(page.extract_text() for page in reader.pages)
        except PyPdfError as exc:
            raise DocumentFieldsUnreadable("PDF text cannot be extracted") from exc
        return DocumentFields(
            first_name=self._read_value(text, FIRST_NAME_LABEL),
            last_name=self._read_value(text, LAST_NAME_LABEL),
        )

    @staticmethod
    def _read_value(text: str, label: str) -> str:
        matches = re.findall(
            rf"^{re.escape(label)}:[ \t]*(.+?)[ \t]*$", text, re.MULTILINE
        )
        if len(matches) != 1:
            raise DocumentFieldsUnreadable(f"Field '{label}' cannot be read")
        return str(matches[0])

    @staticmethod
    def _fit_font_size(line: str, max_width: float) -> float:
        size = FIELD_FONT_SIZE
        while size > MIN_FONT_SIZE and stringWidth(line, FONT, size) > max_width:
            size -= 0.5
        return size

    @staticmethod
    def _with_metadata(pdf: bytes, document_id: str) -> bytes:
        writer = PdfWriter(clone_from=PdfReader(BytesIO(pdf)))
        writer.add_metadata({ID_METADATA_KEY: document_id})
        out = BytesIO()
        _ = writer.write(out)
        return out.getvalue()
