from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database

from app.api.deps import get_db
from app.schemas.analytics import HistoricalAnalyticsResponse
from app.services.analytics import build_historical_analytics

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_model=HistoricalAnalyticsResponse)
@router.get("/historical/analytics", response_model=HistoricalAnalyticsResponse)
def get_historical_analytics(
    station_id: str | None = Query(default=None),
    days: int = Query(default=14, ge=1, le=60),
    db: Database = Depends(get_db),
) -> HistoricalAnalyticsResponse:
    try:
        # Default to first station if station_id is not provided
        if not station_id:
            first_station = db.stations.find_one({})
            if first_station:
                station_id = first_station["_id"]
            else:
                raise ValueError("No stations available in database")
        return build_historical_analytics(db, station_id, days)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
