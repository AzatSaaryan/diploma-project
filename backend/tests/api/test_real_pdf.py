# pyright: reportAny=false
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.adapters.outbound.pdf_stamper import PypdfStamper
from app.bootstrap import create_app
from app.settings import Settings
from tests.api.conftest import AUTH
from tests.fakes import FixedClock
from tests.unit.test_pdf_stamper import make_pdf


@pytest.fixture
def real_client() -> Iterator[TestClient]:
    settings = Settings(api_key=SecretStr("test-key"))
    app = create_app(
        settings,
        stamper=PypdfStamper(settings.public_base_url),
        clock=FixedClock(),
    )
    with TestClient(app) as client:
        yield client


def test_register_and_verify_real_pdf(real_client: TestClient) -> None:
    files = {"file": ("d.pdf", make_pdf(), "application/pdf")}
    registered = real_client.post("/api/v1/documents", files=files, headers=AUTH)
    assert registered.status_code == 200
    stamped = registered.content

    verified = real_client.post(
        "/api/v1/verifications",
        files={"file": ("d.pdf", stamped, "application/pdf")},
    )
    assert verified.json()["status"] == "VALID"
    assert verified.json()["document_id"] == registered.headers["x-document-id"]

    tampered = real_client.post(
        "/api/v1/verifications",
        files={"file": ("d.pdf", stamped + b"\n%tampered", "application/pdf")},
    )
    assert tampered.json()["status"] == "MODIFIED"


def test_unregistered_real_pdf(real_client: TestClient) -> None:
    response = real_client.post(
        "/api/v1/verifications",
        files={"file": ("d.pdf", make_pdf(), "application/pdf")},
    )
    assert response.json()["status"] == "NOT_REGISTERED"
