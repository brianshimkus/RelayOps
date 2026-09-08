import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import Evidence, Tenant
from app.scenarios.generator import MANIFEST_DIR, inject_scenario
from app.scenarios.manifest import load_manifest

SCENARIO_KEYS = sorted(path.stem for path in MANIFEST_DIR.glob("*.yaml"))


def _make_tenant(session: Session, scenario_key: str) -> None:
    manifest = load_manifest(MANIFEST_DIR / f"{scenario_key}.yaml")
    tenant = Tenant(slug=manifest.tenant_slug, name=manifest.tenant_slug, domain="test")
    session.add(tenant)
    session.commit()


def _evidence_content(session: Session, incident_id) -> list[str]:
    query = (
        select(Evidence)
        .where(Evidence.incident_id == incident_id)
        .order_by(Evidence.citation_id)
    )
    return [row.content for row in session.exec(query).all()]


@pytest.mark.parametrize("scenario_key", SCENARIO_KEYS)
def test_same_seed_produces_same_public_content(session: Session, scenario_key: str) -> None:
    _make_tenant(session, scenario_key)

    first = inject_scenario(session, scenario_key, seed=123)
    first_content = _evidence_content(session, first.id)

    second = inject_scenario(session, scenario_key, seed=123)
    second_content = _evidence_content(session, second.id)

    assert first_content == second_content


@pytest.mark.parametrize("scenario_key", SCENARIO_KEYS)
def test_different_seed_varies_content(session: Session, scenario_key: str) -> None:
    _make_tenant(session, scenario_key)

    first = inject_scenario(session, scenario_key, seed=1)
    first_content = _evidence_content(session, first.id)

    second = inject_scenario(session, scenario_key, seed=2)
    second_content = _evidence_content(session, second.id)

    assert first_content != second_content


@pytest.mark.parametrize("scenario_key", SCENARIO_KEYS)
def test_incident_response_does_not_leak_answer(
    client: TestClient, session: Session, scenario_key: str
) -> None:
    _make_tenant(session, scenario_key)

    response = client.post(f"/api/v1/scenarios/{scenario_key}/inject?seed=123")
    assert response.status_code == 201

    text = response.text.lower()
    assert "root_cause" not in text
    assert "approved_tools" not in text
    assert "prohibited_tools" not in text
    assert "recovery_check" not in text
