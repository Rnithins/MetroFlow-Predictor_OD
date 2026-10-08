from __future__ import annotations

from pydantic import BaseModel


class StationOut(BaseModel):
    id: str
    code: str
    name: str
    line: str
    zone: str | None = None
    latitude: float
    longitude: float
    baseline_capacity: int
    is_interchange: bool
    state: str | None = None
    district: str | None = None
    city: str
    country: str = "India"
    operational_status: str = "OPERATIONAL"
    system_code: str | None = None
    agency_name: str | None = None
