from app.adapters.outbound.in_memory_registry import InMemoryRegistry
from app.application.ports.clock import Clock
from app.application.ports.pdf_stamper import PdfStamper
from app.application.ports.registry import Registry
from tests.fakes import FailingRegistry, FakePdfStamper, FixedClock


def test_adapters_satisfy_ports() -> None:
    clock: Clock = FixedClock()
    registries: list[Registry] = [
        InMemoryRegistry("0xissuer", clock),
        FailingRegistry(),
    ]
    stamper: PdfStamper = FakePdfStamper()
    assert len(registries) == 2
    assert stamper.extract_id(stamper.stamp(b"%PDF-", "ab")) == "ab"
