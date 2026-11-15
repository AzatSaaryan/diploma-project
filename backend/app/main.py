from app.adapters.outbound.pdf_stamper import PypdfStamper
from app.bootstrap import create_app
from app.settings import Settings

_settings = Settings()  # pyright: ignore[reportCallIssue]
app = create_app(_settings, stamper=PypdfStamper(_settings.public_base_url))
