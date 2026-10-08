from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class OperationalStatus(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    UNDER_CONSTRUCTION = "UNDER_CONSTRUCTION"
    PROPOSED = "PROPOSED"
    TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class DataProvenance(str, Enum):
    REALTIME = "REALTIME"
    HISTORICAL = "HISTORICAL"
    SIMULATED = "SIMULATED"
    PREDICTED = "PREDICTED"


class MetroAgencyOut(BaseModel):
    id: str
    code: str
    name: str
    city: str
    state: str
    country: str = "India"
    operational_status: OperationalStatus = OperationalStatus.OPERATIONAL
    lines_count: int = 0
    stations_count: int = 0
    fleet_size: int = 0


class MetroLineOut(BaseModel):
    id: str
    system_code: str
    name: str
    color_hex: str
    status: OperationalStatus = OperationalStatus.OPERATIONAL
    stations_count: int = 0
    length_km: float = 0.0


class StationHierarchyOut(BaseModel):
    id: str
    code: str
    name: str
    system_code: str
    agency_name: str
    line: str
    zone: str | None = None
    latitude: float
    longitude: float
    baseline_capacity: int
    is_interchange: bool
    operational_status: OperationalStatus = OperationalStatus.OPERATIONAL
    country: str = "India"
    state: str
    district: str
    city: str


class StationConnectionOut(BaseModel):
    id: str
    system_code: str
    from_station_id: str
    to_station_id: str
    line: str
    distance_km: float
    travel_time_minutes: float
    operational_status: OperationalStatus = OperationalStatus.OPERATIONAL


class CityHierarchySummary(BaseModel):
    name: str = ""
    state: str
    district: str
    country: str = "India"
    agency_name: str
    agency_code: str
    stations_count: int
    lines_count: int
    operational_lines: list[str]
    under_construction_lines: list[str] = []
    operational_stations: int
    under_construction_stations: int
    proposed_stations: int


class NationalHierarchyOverview(BaseModel):
    country: str = "India"
    total_metro_systems: int
    total_cities: int
    total_states: int
    total_lines: int
    total_stations: int
    operational_stations: int
    under_construction_stations: int
    proposed_stations: int
    systems: list[MetroAgencyOut]
    cities: list[CityHierarchySummary]
