# pyright: reportAny=false
from fastapi.testclient import TestClient

from app.application.ports.registry import Registry
from app.bootstrap import create_app
from app.settings import Settings
from tests.api.conftest import AUTH, PDF
from tests.fakes import FailingRegistry, FakePdfStamper, FixedClock


def upload(data: bytes) -> dict[str, tuple[str, bytes, str]]:
    return {"file": ("doc.pdf", data, "application/pdf")}


def register(client: TestClient) -> tuple[str, bytes]:
    response = client.post("/api/v1/documents", files=upload(PDF), headers=AUTH)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["x-transaction-hash"].startswith("0x")
    return response.headers["x-document-id"], response.content


def test_full_cycle(client: TestClient) -> None:
    document_id, pdf = register(client)

    verified = client.post("/api/v1/verifications", files=upload(pdf))
    assert verified.status_code == 200
    assert verified.json()["status"] == "VALID"
    assert verified.json()["document_id"] == document_id

    by_id = client.get(f"/api/v1/verifications/{document_id}")
    assert by_id.json()["status"] == "VALID"
    assert by_id.json()["issuer"] == "in-memory-issuer"

    revoked = client.post(f"/api/v1/documents/{document_id}/revoke", headers=AUTH)
    assert revoked.status_code == 200
    assert revoked.json()["transaction_hash"].startswith("0x")

    again = client.post(f"/api/v1/documents/{document_id}/revoke", headers=AUTH)
    assert again.status_code == 200
    assert again.json()["transaction_hash"] is None

    after = client.post("/api/v1/verifications", files=upload(pdf))
    assert after.json()["status"] == "REVOKED"


def test_modified_file(client: TestClient) -> None:
    _, pdf = register(client)

    response = client.post("/api/v1/verifications", files=upload(b"%PDF-9" + pdf[6:]))

    assert response.json()["status"] == "MODIFIED"


def test_unknown_id_is_200_not_registered(client: TestClient) -> None:
    response = client.get(f"/api/v1/verifications/{'0' * 32}")

    assert response.status_code == 200
    assert response.json()["status"] == "NOT_REGISTERED"


def test_malformed_id_is_422(client: TestClient) -> None:
    assert client.get("/api/v1/verifications/XYZ").status_code == 422


def test_missing_api_key_is_401(client: TestClient) -> None:
    response = client.post("/api/v1/documents", files=upload(PDF))
    assert response.status_code == 401


def test_wrong_api_key_is_401(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents", files=upload(PDF), headers={"X-API-Key": "nope"}
    )
    assert response.status_code == 401


def test_revoke_requires_api_key(client: TestClient) -> None:
    assert client.post(f"/api/v1/documents/{'0' * 32}/revoke").status_code == 401


def test_non_pdf_is_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents", files=upload(b"hello world"), headers=AUTH
    )
    assert response.status_code == 422


def test_too_large_is_413(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents", files=upload(b"%PDF-" + b"0" * 2000), headers=AUTH
    )
    assert response.status_code == 413


def test_revoke_unknown_is_404(client: TestClient) -> None:
    response = client.post(f"/api/v1/documents/{'0' * 32}/revoke", headers=AUTH)
    assert response.status_code == 404


def test_naive_expires_at_is_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents",
        files=upload(PDF),
        data={"expires_at": "2030-01-01T00:00:00"},
        headers=AUTH,
    )
    assert response.status_code == 422


def test_expiry(client: TestClient, clock: FixedClock) -> None:
    from datetime import timedelta

    response = client.post(
        "/api/v1/documents",
        files=upload(PDF),
        data={"expires_at": (clock.now + timedelta(days=1)).isoformat()},
        headers=AUTH,
    )
    document_id = response.headers["x-document-id"]
    assert (
        client.get(f"/api/v1/verifications/{document_id}").json()["status"] == "VALID"
    )

    clock.now += timedelta(days=2)

    assert (
        client.get(f"/api/v1/verifications/{document_id}").json()["status"] == "EXPIRED"
    )


def test_registry_down_is_503(settings: Settings) -> None:
    failing: Registry = FailingRegistry()
    app = create_app(
        settings, stamper=FakePdfStamper(), registry=failing, clock=FixedClock()
    )
    with TestClient(app) as client:
        assert (
            client.post(
                "/api/v1/documents", files=upload(PDF), headers=AUTH
            ).status_code
            == 503
        )
        assert client.get(f"/api/v1/verifications/{'0' * 32}").status_code == 503
