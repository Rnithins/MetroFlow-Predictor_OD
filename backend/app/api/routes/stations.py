from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pymongo.database import Database

from app.api.deps import get_db
from app.schemas.station import StationOut
from app.services.documents import with_public_id

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("", response_model=list[StationOut])
@router.get("/", response_model=list[StationOut])
def get_stations(
    city: str | None = Query(default=None),
    db: Database = Depends(get_db),
) -> list[StationOut]:
    query = {}
    if city:
        query["city"] = city
    stations = list(db.stations.find(query).sort("name", 1))
    return [StationOut(**with_public_id(station)) for station in stations]
