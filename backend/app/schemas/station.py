from pydantic import BaseModel


class StationOut(BaseModel):
    id: str
    code: str
    name: str
    line: str
    zone: str
    latitude: float
    longitude: float
    baseline_capacity: int
    is_interchange: bool
