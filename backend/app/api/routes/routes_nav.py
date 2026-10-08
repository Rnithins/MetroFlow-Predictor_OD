from __future__ import annotations

from fastapi import APIRouter, Query, Depends
from pymongo.database import Database
from app.api.deps import get_db
from app.services.routes_engine import (
    recommend_routes,
    compute_cumulative_segment_loads,
    get_smart_journey_advisory,
)

router = APIRouter(tags=["routes"])


@router.get("/routes")
def get_route_recommendation(
    origin: str = Query("Rajiv Chowk", description="Origin Station Name or Code"),
    destination: str = Query("Noida Sector 62", description="Destination Station Name or Code"),
) -> dict:
    """
    Route Recommendation API:
    Given Origin and Destination, computes Best Route, Fastest Route,
    Least Crowded Route, and Cheapest Route with seat availability probabilities.
    """
    return recommend_routes(origin=origin, destination=destination)


@router.get("/routes/segment-loads")
def get_segment_loads(
    city: str = Query("Delhi", description="Metro City Name"),
    db: Database = Depends(get_db),
) -> dict:
    """
    Cumulative Segment Load API:
    Computes aggregated passenger volumes across physical network corridors from OD flow matrices.
    Tags corridors as NORMAL (<70%), WARNING (70-90%), or CRITICAL (>90%).
    """
    return compute_cumulative_segment_loads(db=db, city=city)


@router.get("/routes/advisory")
def get_journey_advisory(
    origin: str = Query("Rajiv Chowk", description="Origin Station Name or Code"),
    destination: str = Query("Noida Sector 62", description="Destination Station Name or Code"),
    db: Database = Depends(get_db),
) -> dict:
    """
    Passenger-Facing Smart Journey Advisory:
    Returns predicted train fullness, wait vs board advisory, alternative route suggestions,
    and optimal boarding coach recommendations.
    """
    return get_smart_journey_advisory(origin=origin, destination=destination, db=db)
