# pyright: reportAny=false
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.application.ports.registry import Registry
from app.bootstrap import create_app
from app.settings import Settings
from tests.api.conftest import AUTH, BOB
from tests.fakes import FailingRegistry, FakePdfRenderer, FixedClock, fake_pdf

UNKNOWN_ID = "0" * 32


def upload(data: bytes) -> dict[str, tuple[str, bytes, str]]:
    return {"file": ("doc.pdf", data, "application/pdf")}


def register(client: TestClient, body: dict[str, str] = BOB) -> tuple[str, bytes]:
    response = client.post("/api/v1/documents", json=body, headers=AUTH)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["x-transaction-hash"].startswith("0x")
    return response.headers["x-document-id"], response.content


def test_full_cycle_by_file(client: TestClient) -> None:
    document_id, pdf = register(client)

    verified = client.post("/api/v1/verifications", files=upload(pdf))
    assert verified.status_code == 200
    body = verified.json()
    assert body["status"] == "VALID"
    assert body["document_id"] == document_id
    assert body["first_name"] == "Bob"
    assert body["last_name"] == "Smith"
    assert body["issuer"] == "in-memory-issuer"

    revoked = client.post(f"/api/v1/documents/{document_id}/revoke", headers=AUTH)
    assert revoked.status_code == 200
    assert revoked.json() == {"document_id": document_id, "revoked": True}

    again = client.post(f"/api/v1/documents/{document_id}/revoke", headers=AUTH)
    assert again.json() == {"document_id": document_id, "revoked": True}

    after = client.post("/api/v1/verifications", files=upload(pdf))
    assert after.json()["status"] == "REVOKED"


def test_full_cycle_by_qr(client: TestClient) -> None:
    document_id, _ = register(client)

    lookup = client.post(f"/api/v1/verifications/{document_id}/lookup")
    assert lookup.status_code == 200
    assert lookup.json() == {"document_id": document_id, "registered": True}

    valid = client.post(
        f"/api/v1/verifications/{document_id}",
        json={"first_name": "bob", "last_name": " SMITH "},
    )
    assert valid.json()["status"] == "VALID"

    wrong = client.post(
        f"/api/v1/verifications/{document_id}",
        json={"first_name": "Alice", "last_name": "Smith"},
    )
    assert wrong.json()["status"] == "MODIFIED"


def test_lookup_unknown(client: TestClient) -> None:
    response = client.post(f"/api/v1/verifications/{UNKNOWN_ID}/lookup")

    assert response.status_code == 200
    assert response.json()["registered"] is False


def test_manual_unknown_is_not_registered(client: TestClient) -> None:
    response = client.post(f"/api/v1/verifications/{UNKNOWN_ID}", json=BOB)

    assert response.status_code == 200
    assert response.json()["status"] == "NOT_REGISTERED"


def test_file_with_changed_name_is_modified(client: TestClient) -> None:
    document_id, _ = register(client)
    forged = fake_pdf(document_id, "Alice", "Smith")

    response = client.post("/api/v1/verifications", files=upload(forged))

    assert response.json()["status"] == "MODIFIED"
    assert response.json()["first_name"] == "Alice"


def test_file_with_unreadable_fields_is_500(client: TestClient) -> None:
    document_id, _ = register(client)
    broken = f"%PDF-fake\nID:{document_id}\n".encode()

    response = client.post("/api/v1/verifications", files=upload(broken))

    assert response.status_code == 500


def test_malformed_id_is_422(client: TestClient) -> None:
    assert client.post("/api/v1/verifications/XYZ/lookup").status_code == 422
    assert client.post("/api/v1/verifications/XYZ", json=BOB).status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        {"first_name": "", "last_name": "Smith"},
        {"first_name": "Bob"},
        {"first_name": "Боб", "last_name": "Smith"},
        {"first_name": "Bob", "last_name": "Smith: Jr"},
        {"first_name": "B" * 65, "last_name": "Smith"},
    ],
)
def test_invalid_fields_are_422(client: TestClient, body: dict[str, str]) -> None:
    response = client.post("/api/v1/documents", json=body, headers=AUTH)
    assert response.status_code == 422


def test_missing_api_key_is_401(client: TestClient) -> None:
    assert client.post("/api/v1/documents", json=BOB).status_code == 401


def test_wrong_api_key_is_401(client: TestClient) -> None:
    response = client.post("/api/v1/documents", json=BOB, headers={"X-API-Key": "nope"})
    assert response.status_code == 401


def test_revoke_requires_api_key(client: TestClient) -> None:
    assert client.post(f"/api/v1/documents/{UNKNOWN_ID}/revoke").status_code == 401


def test_non_pdf_is_422(client: TestClient) -> None:
    response = client.post("/api/v1/verifications", files=upload(b"hello"))
    assert response.status_code == 422


def test_too_large_is_413(client: TestClient) -> None:
    response = client.post(
        "/api/v1/verifications", files=upload(b"%PDF-" + b"0" * 2000)
    )
    assert response.status_code == 413


def test_revoke_unknown_is_404(client: TestClient) -> None:
    response = client.post(f"/api/v1/documents/{UNKNOWN_ID}/revoke", headers=AUTH)
    assert response.status_code == 404


def test_naive_expires_at_is_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents",
        json={**BOB, "expires_at": "2030-01-01T00:00:00"},
        headers=AUTH,
    )
    assert response.status_code == 422


def test_expiry(client: TestClient, clock: FixedClock) -> None:
    expires_at = (clock.now + timedelta(days=1)).isoformat()
    document_id, _ = register(client, {**BOB, "expires_at": expires_at})
    url = f"/api/v1/verifications/{document_id}"

    assert client.post(url, json=BOB).json()["status"] == "VALID"

    clock.now += timedelta(days=2)

    assert client.post(url, json=BOB).json()["status"] == "EXPIRED"


def test_registry_down_is_503(settings: Settings) -> None:
    failing: Registry = FailingRegistry()
    app = create_app(
        settings, renderer=FakePdfRenderer(), registry=failing, clock=FixedClock()
    )
    with TestClient(app) as client:
        register_response = client.post("/api/v1/documents", json=BOB, headers=AUTH)
        lookup_response = client.post(f"/api/v1/verifications/{UNKNOWN_ID}/lookup")
        assert register_response.status_code == 503
        assert lookup_response.status_code == 503
