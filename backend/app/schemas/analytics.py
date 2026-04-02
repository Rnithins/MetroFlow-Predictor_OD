from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.flow import PassengerFlowOut, PredictionResponse


class DashboardKpi(BaseModel):
    label: str
    value: str
    change: str
    tone: Literal["neutral", "good", "warning", "critical"] = "neutral"


class DashboardTrendPoint(BaseModel):
    label: str
    actual: int | None = None
    forecast: int | None = None


class DashboardBreakdownPoint(BaseModel):
    label: str
    value: int


class DashboardHeatmapRow(BaseModel):
    day_label: str
    values: list[int]


class DashboardAlert(BaseModel):
    title: str
    detail: str
    severity: Literal["normal", "warning", "critical"]
    timestamp: datetime


class DashboardOverviewResponse(BaseModel):
    generated_at: datetime
    selected_station_id: str
    selected_station_name: str
    model_version: str
    insight: str
    kpis: list[DashboardKpi]
    trend: list[DashboardTrendPoint]
    hourly_distribution: list[DashboardBreakdownPoint]
    heatmap: list[DashboardHeatmapRow]
    recent_flows: list[PassengerFlowOut]
    recent_predictions: list[PredictionResponse]
    alerts: list[DashboardAlert]


class HistoricalSeriesPoint(BaseModel):
    label: str
    total_passengers: int


class HistoricalAnalyticsResponse(BaseModel):
    generated_at: datetime
    station_id: str
    station_name: str
    days: int
    daily_totals: list[HistoricalSeriesPoint]
    hourly_average: list[DashboardBreakdownPoint]
    heatmap: list[DashboardHeatmapRow]
    latest_records: list[PassengerFlowOut]
