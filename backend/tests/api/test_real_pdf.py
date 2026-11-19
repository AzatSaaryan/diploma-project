# pyright: reportAny=false
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.adapters.outbound.pdf_renderer import ReportlabPdfRenderer
from app.bootstrap import create_app
from app.domain.fields import DocumentFields
from app.settings import Settings
from tests.api.conftest import AUTH, BOB
from tests.fakes import FixedClock


@pytest.fixture
def renderer() -> ReportlabPdfRenderer:
    return ReportlabPdfRenderer("http://localhost:8000")


@pytest.fixture
def real_client(renderer: ReportlabPdfRenderer) -> Iterator[TestClient]:
    app = create_app(
        Settings(api_key=SecretStr("test-key")),
        renderer=renderer,
        clock=FixedClock(),
    )
    with TestClient(app) as client:
        yield client


def verify(client: TestClient, pdf: bytes) -> dict[str, str]:
    files = {"file": ("d.pdf", pdf, "application/pdf")}
    response = client.post("/api/v1/verifications", files=files)
    assert response.status_code == 200, response.text
    return response.json()


def test_register_and_verify_real_pdf(real_client: TestClient) -> None:
    registered = real_client.post("/api/v1/documents", json=BOB, headers=AUTH)
    assert registered.status_code == 200

    body = verify(real_client, registered.content)

    assert body["status"] == "VALID"
    assert body["document_id"] == registered.headers["x-document-id"]
    assert body["first_name"] == "Bob"


def test_visible_name_change_is_modified(
    real_client: TestClient, renderer: ReportlabPdfRenderer
) -> None:
    registered = real_client.post("/api/v1/documents", json=BOB, headers=AUTH)
    document_id = registered.headers["x-document-id"]
    forged = renderer.render(DocumentFields("Alice", "Smith"), document_id)

    assert verify(real_client, forged)["status"] == "MODIFIED"


def test_unregistered_real_pdf(
    real_client: TestClient, renderer: ReportlabPdfRenderer
) -> None:
    pdf = renderer.render(DocumentFields("Bob", "Smith"), "0" * 32)

    assert verify(real_client, pdf)["status"] == "NOT_REGISTERED"
