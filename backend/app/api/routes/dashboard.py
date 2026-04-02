from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database

from app.api.deps import get_current_user, get_db
from app.schemas.analytics import DashboardOverviewResponse
from app.services.analytics import build_dashboard_overview

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    station_id: str | None = Query(default=None),
    db: Database = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> DashboardOverviewResponse:
    try:
        return build_dashboard_overview(db, station_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
