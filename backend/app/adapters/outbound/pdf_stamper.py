# pyright: reportAny=false, reportUnknownMemberType=false
from io import BytesIO
from typing import final

import qrcode
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PyPdfError
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from app.domain.errors import InvalidDocumentFile

ID_METADATA_KEY = "/DocumentId"
QR_SIZE_PT = 70.0
QR_MARGIN_PT = 24.0


@final
class PypdfStamper:
    """Puts a QR code on the first page and the document ID into PDF metadata."""

    def __init__(self, public_base_url: str) -> None:
        self._base_url = public_base_url.rstrip("/")

    def stamp(self, pdf: bytes, document_id: str) -> bytes:
        try:
            reader = PdfReader(BytesIO(pdf))
            if reader.is_encrypted or len(reader.pages) == 0:
                raise InvalidDocumentFile("PDF is encrypted or has no pages")
            writer = PdfWriter(clone_from=reader)
        except PyPdfError as exc:
            raise InvalidDocumentFile("PDF cannot be parsed") from exc

        page = writer.pages[0]
        left = float(page.mediabox.left)
        bottom = float(page.mediabox.bottom)
        width = float(page.mediabox.width)
        overlay = self._qr_overlay(
            f"{self._base_url}/api/v1/verifications/{document_id}",
            x=left + width - QR_SIZE_PT - QR_MARGIN_PT,
            y=bottom + QR_MARGIN_PT,
            page_width=left + width,
            page_height=bottom + float(page.mediabox.height),
        )
        page.merge_page(PdfReader(BytesIO(overlay)).pages[0])
        writer.add_metadata({ID_METADATA_KEY: document_id})

        out = BytesIO()
        _ = writer.write(out)
        return out.getvalue()

    def extract_id(self, pdf: bytes) -> str | None:
        try:
            metadata = PdfReader(BytesIO(pdf)).metadata
        except PyPdfError:
            return None
        if metadata is None:
            return None
        value = metadata.get(ID_METADATA_KEY)
        return str(value) if value is not None else None

    @staticmethod
    def _qr_overlay(
        url: str, *, x: float, y: float, page_width: float, page_height: float
    ) -> bytes:
        image = qrcode.make(url).get_image()
        buffer = BytesIO()
        canvas = Canvas(buffer, pagesize=(page_width, page_height))
        _ = canvas.drawImage(ImageReader(image), x, y, QR_SIZE_PT, QR_SIZE_PT)
        canvas.save()
        return buffer.getvalue()
