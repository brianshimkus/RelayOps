from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel


class IncidentCreate(SQLModel):
    tenant_id: UUID
    title: str
    summary: str
    severity: str = "medium"


class IncidentRead(SQLModel):
    id: UUID
    tenant_id: UUID
    scenario_key: str | None
    title: str
    summary: str
    severity: str
    status: str
    created_at: datetime
    updated_at: datetime

class EvidenceRead(SQLModel):
    citation_id: str
    kind: str
    source: str
    content: str
    observed_at: datetime