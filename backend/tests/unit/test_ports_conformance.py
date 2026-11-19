from app.adapters.outbound.in_memory_registry import InMemoryRegistry
from app.adapters.outbound.pdf_renderer import ReportlabPdfRenderer
from app.application.ports.clock import Clock
from app.application.ports.pdf_renderer import PdfRenderer
from app.application.ports.registry import Registry
from tests.fakes import FailingRegistry, FakePdfRenderer, FixedClock


def test_adapters_satisfy_ports() -> None:
    clock: Clock = FixedClock()
    registries: list[Registry] = [
        InMemoryRegistry("0xissuer", clock),
        FailingRegistry(),
    ]
    renderers: list[PdfRenderer] = [
        FakePdfRenderer(),
        ReportlabPdfRenderer("http://localhost"),
    ]
    assert len(registries) == 2
    assert len(renderers) == 2
