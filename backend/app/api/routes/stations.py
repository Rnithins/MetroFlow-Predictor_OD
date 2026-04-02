from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.api.deps import get_current_user, get_db
from app.schemas.station import StationOut
from app.services.documents import with_public_id

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("", response_model=list[StationOut])
def get_stations(
    db: Database = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[StationOut]:
    stations = list(db.stations.find({}).sort("name", 1))
    return [StationOut(**with_public_id(station)) for station in stations]
