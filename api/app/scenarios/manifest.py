from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class EvidenceSpec(BaseModel):
    kind: str
    source: str
    template: str
    required: bool = False
    misleading: bool = False


class ScenarioManifest(BaseModel):
    key: str
    tenant_slug: str
    title: str
    summary: str
    severity: str
    root_cause: str
    evidence: list[EvidenceSpec]
    approved_tools: list[str]
    prohibited_tools: list[str]
    recovery_check: str
    communication_facts: list[str] = Field(default_factory=list)


def load_manifest(path: Path) -> ScenarioManifest:
    return ScenarioManifest.model_validate(yaml.safe_load(path.read_text()))