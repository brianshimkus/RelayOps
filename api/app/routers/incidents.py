from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.database import get_session
from app.models import Incident
from app.schemas import IncidentCreate, IncidentRead

router = APIRouter(prefix="/incidents", tags=["incidents"])
Db = Annotated[Session, Depends(get_session)]


@router.post("", response_model=IncidentRead, status_code=201)
def create_incident(payload: IncidentCreate, db: Db) -> Incident:
    incident = Incident.model_validate(payload)
    db.add(incident)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid tenant_id: tenant does not exist")
    db.refresh(incident)
    return incident


@router.get("", response_model=list[IncidentRead])
def list_incidents(db: Db) -> list[Incident]:
    query = select(Incident).order_by(Incident.created_at.desc())
    return list(db.exec(query).all())


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(incident_id: UUID, db: Db) -> Incident:
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident