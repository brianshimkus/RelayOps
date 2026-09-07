from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Tenant(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    slug: str = Field(index=True, unique=True)
    name: str
    domain: str
    created_at: datetime = Field(default_factory=now_utc)


class Incident(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenant.id", index=True)
    scenario_key: str | None = Field(default=None, index=True)
    seed: int | None = None
    title: str
    summary: str
    severity: str = "medium"
    status: str = Field(default="open", index=True)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class Evidence(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    incident_id: UUID = Field(foreign_key="incident.id", index=True)
    citation_id: str = Field(index=True)
    kind: str
    source: str
    content: str
    observed_at: datetime = Field(default_factory=now_utc)


class Hypothesis(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    incident_id: UUID = Field(foreign_key="incident.id", index=True)
    rank: int
    cause: str
    confidence: float
    support_ids: list[str] = Field(sa_column=Column(JSON))
    contradict_ids: list[str] = Field(sa_column=Column(JSON))


class ActionProposal(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    incident_id: UUID = Field(foreign_key="incident.id", index=True)
    tool_name: str
    arguments: dict[str, Any] = Field(sa_column=Column(JSON))
    risk_tier: str
    status: str = "proposed"
    payload_hash: str = Field(index=True)
    idempotency_key: str = Field(index=True, unique=True)
    rollback_plan: str


class Approval(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    proposal_id: UUID = Field(foreign_key="actionproposal.id", index=True)
    payload_hash: str
    approved_by: str
    status: str = "approved"
    approved_at: datetime = Field(default_factory=now_utc)
    consumed_at: datetime | None = None


class AuditEvent(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True)
    incident_id: UUID | None = Field(default=None, index=True)
    event_type: str
    actor: str
    payload: dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=now_utc)