from datetime import UTC, datetime

from fastapi import APIRouter, FastAPI

from app.adapters.inbound.api import documents, verifications
from app.adapters.inbound.api.errors import register_error_handlers
from app.adapters.outbound.in_memory_registry import InMemoryRegistry
from app.application.ports.clock import Clock
from app.application.ports.pdf_stamper import PdfStamper
from app.application.ports.registry import Registry
from app.settings import Settings


def utc_now() -> datetime:
    return datetime.now(UTC)


def create_app(
    settings: Settings,
    *,
    stamper: PdfStamper,
    registry: Registry | None = None,
    clock: Clock = utc_now,
) -> FastAPI:
    """Composition root: wires adapters into ports."""
    app = FastAPI(title="Document verification")
    app.state.settings = settings
    app.state.clock = clock
    app.state.stamper = stamper
    app.state.registry = registry or InMemoryRegistry(settings.issuer, clock)

    api_v1 = APIRouter(prefix="/api/v1")
    api_v1.include_router(documents.router)
    api_v1.include_router(verifications.router)
    app.include_router(api_v1)
    register_error_handlers(app)
    return app
