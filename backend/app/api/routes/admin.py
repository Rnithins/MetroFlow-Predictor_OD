from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database

from app.api.deps import get_db, require_admin
from app.schemas.flow import PassengerFlowCreate, PassengerFlowOut, PassengerFlowUpdate
from app.services.documents import new_id

router = APIRouter(prefix="/admin", tags=["admin"])


def _station_map(db: Database) -> dict[str, dict]:
    return {station["_id"]: station for station in db.stations.find({})}


def _flow_response(flow: dict, station: dict) -> PassengerFlowOut:
    return PassengerFlowOut(
        id=flow["_id"],
        station_id=flow["station_id"],
        station_name=station["name"],
        line=station["line"],
        timestamp=flow["timestamp"],
        passenger_count=flow["passenger_count"],
        avg_dwell_minutes=flow["avg_dwell_minutes"],
        weather_code=flow["weather_code"],
        event_flag=flow["event_flag"],
        event_name=flow.get("event_name"),
        source=flow["source"],
    )


@router.get("/flows", response_model=list[PassengerFlowOut])
def list_flows(
    db: Database = Depends(get_db),
    _: dict = Depends(require_admin),
) -> list[PassengerFlowOut]:
    station_map = _station_map(db)
    flows = list(db.passenger_flows.find({}).sort("timestamp", -1).limit(25))
    return [_flow_response(flow, station_map[flow["station_id"]]) for flow in flows]


@router.post("/flows", response_model=PassengerFlowOut, status_code=status.HTTP_201_CREATED)
def create_flow(
    payload: PassengerFlowCreate,
    db: Database = Depends(get_db),
    _: dict = Depends(require_admin),
) -> PassengerFlowOut:
    station = db.stations.find_one({"_id": payload.station_id})
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")

    flow = {"_id": new_id(), **payload.model_dump()}
    db.passenger_flows.insert_one(flow)
    return _flow_response(flow, station)


@router.put("/flows/{flow_id}", response_model=PassengerFlowOut)
def update_flow(
    flow_id: str,
    payload: PassengerFlowUpdate,
    db: Database = Depends(get_db),
    _: dict = Depends(require_admin),
) -> PassengerFlowOut:
    updates = {key: value for key, value in payload.model_dump().items() if value is not None}
    existing = db.passenger_flows.find_one({"_id": flow_id})
    if existing is None:
        raise HTTPException(status_code=404, detail="Flow record not found")

    if updates:
        db.passenger_flows.update_one({"_id": flow_id}, {"$set": updates})
    refreshed = db.passenger_flows.find_one({"_id": flow_id})
    station = db.stations.find_one({"_id": refreshed["station_id"]})
    return _flow_response(refreshed, station)


@router.delete("/flows/{flow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flow(
    flow_id: str,
    db: Database = Depends(get_db),
    _: dict = Depends(require_admin),
) -> None:
    result = db.passenger_flows.delete_one({"_id": flow_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Flow record not found")
