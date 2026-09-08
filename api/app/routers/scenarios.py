from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.scenarios.generator import inject_scenario
from app.schemas import IncidentRead

router = APIRouter(prefix="/scenarios", tags=["scenarios"])
Db = Annotated[Session, Depends(get_session)]


@router.post("/{key}/inject", response_model=IncidentRead, status_code=201)
def inject(key: str, db: Db, seed: int = Query(1001)) -> IncidentRead:
    return inject_scenario(db, key, seed)