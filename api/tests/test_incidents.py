from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import Tenant


def _make_tenant(session: Session) -> Tenant:
    tenant = Tenant(slug=f"test-{uuid4().hex[:8]}", name="Test Tenant", domain="test")
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    return tenant


def test_create_incident(client: TestClient, session: Session) -> None:
    tenant = _make_tenant(session)
    response = client.post(
        "/api/v1/incidents",
        json={
            "tenant_id": str(tenant.id),
            "title": "Test incident",
            "summary": "Created during automated test",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Test incident"
    assert body["status"] == "open"


def test_create_incident_rejects_unknown_tenant(client: TestClient) -> None:
    response = client.post(
        "/api/v1/incidents",
        json={
            "tenant_id": str(uuid4()),
            "title": "Should fail",
            "summary": "Tenant does not exist",
        },
    )
    assert response.status_code == 400


def test_list_and_get_incident(client: TestClient, session: Session) -> None:
    tenant = _make_tenant(session)
    created = client.post(
        "/api/v1/incidents",
        json={
            "tenant_id": str(tenant.id),
            "title": "Listed incident",
            "summary": "Should appear in list and get",
        },
    ).json()

    listed = client.get("/api/v1/incidents")
    assert listed.status_code == 200
    assert any(item["id"] == created["id"] for item in listed.json())

    fetched = client.get(f"/api/v1/incidents/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Listed incident"