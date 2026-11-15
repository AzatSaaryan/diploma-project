from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.adapters.outbound.in_memory_registry import InMemoryRegistry
from app.bootstrap import create_app
from app.settings import Settings
from tests.fakes import FakePdfStamper, FixedClock

API_KEY = "test-key"
AUTH = {"X-API-Key": API_KEY}
PDF = b"%PDF-1.7\nhello"


@pytest.fixture
def settings() -> Settings:
    return Settings(api_key=SecretStr(API_KEY), max_file_size_bytes=1024)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()


@pytest.fixture
def client(settings: Settings, clock: FixedClock) -> Iterator[TestClient]:
    app = create_app(
        settings,
        stamper=FakePdfStamper(),
        registry=InMemoryRegistry(settings.issuer, clock),
        clock=clock,
    )
    with TestClient(app) as test_client:
        yield test_client
