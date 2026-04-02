from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database

from app.api.deps import get_current_user, get_db
from app.schemas.analytics import HistoricalAnalyticsResponse
from app.services.analytics import build_historical_analytics

router = APIRouter(prefix="/historical", tags=["historical"])


@router.get("/analytics", response_model=HistoricalAnalyticsResponse)
def get_historical_analytics(
    station_id: str,
    days: int = Query(default=14, ge=3, le=30),
    db: Database = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> HistoricalAnalyticsResponse:
    try:
        return build_historical_analytics(db, station_id, days)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
