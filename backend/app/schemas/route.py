from pydantic import BaseModel, Field


class RouteStation(BaseModel):
    id: str
    code: str
    name: str
    line: str
    latitude: float
    longitude: float
    baseline_capacity: int
    is_interchange: bool
    current_flow: int
    load_level: str
    operational_status: str = "OPERATIONAL"


class RouteOptimizeRequest(BaseModel):
    origin_station_id: str
    destination_station_id: str
    avoid_congestion: bool = False
    include_planned_lines: bool = False


class RouteOptimizeResponse(BaseModel):
    path: list[RouteStation]
    total_stations: int
    interchanges: list[str]
    estimated_duration_minutes: float
    congestion_index: float
    alternative_path: list[RouteStation] | None = None
    alternative_duration_minutes: float | None = None
    alternative_congestion_index: float | None = None
