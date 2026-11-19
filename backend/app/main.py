from app.adapters.outbound.pdf_renderer import ReportlabPdfRenderer
from app.bootstrap import create_app
from app.settings import Settings

_settings = Settings()  # pyright: ignore[reportCallIssue]
app = create_app(_settings, renderer=ReportlabPdfRenderer(_settings.public_base_url))
