from datetime import UTC, datetime, timedelta
from pathlib import Path
from random import Random

from sqlmodel import Session, select

from app.models import Evidence, Incident, Tenant
from app.scenarios.manifest import load_manifest

MANIFEST_DIR = Path(__file__).resolve().parents[3] / "scenarios" / "private" / "manifests"


def inject_scenario(db: Session, key: str, seed: int) -> Incident:
    manifest = load_manifest(MANIFEST_DIR / f"{key}.yaml")
    tenant = db.exec(select(Tenant).where(Tenant.slug == manifest.tenant_slug)).one()

    rng = Random(seed)
    started = datetime.now(UTC).replace(microsecond=0)
    values = {
        "started_at": started.isoformat(),
        "token_age": rng.randint(31, 45),
        "expired_at": (started - timedelta(hours=rng.randint(1, 12))).isoformat(),
        "event_id": f"evt_{rng.randint(100000, 999999)}",
        "batch_id": f"batch_{rng.randint(1000, 9999)}",
        "schema_version": f"{rng.randint(2, 5)}.0",
        "mismatch_cents": rng.randint(500, 25000),
        "queue_depth": rng.randint(200, 2000),
        "retry_count": rng.randint(3, 8),
    }

    incident = Incident(
        tenant_id=tenant.id,
        scenario_key=manifest.key,
        seed=seed,
        title=manifest.title,
        summary=manifest.summary,
        severity=manifest.severity,
    )
    db.add(incident)
    db.flush()

    for index, spec in enumerate(manifest.evidence, start=1):
        db.add(Evidence(
            incident_id=incident.id,
            citation_id=f"E{index:03d}",
            kind=spec.kind,
            source=spec.source,
            content=spec.template.format(**values),
        ))

    db.commit()
    db.refresh(incident)
    return incident