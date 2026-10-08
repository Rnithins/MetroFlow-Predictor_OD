from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PassengerFlowOut(BaseModel):
    id: str
    station_id: str
    station_name: str
    line: str
    timestamp: datetime
    passenger_count: int
    avg_dwell_minutes: float
    weather_code: str
    event_flag: bool
    event_name: str | None = None
    source: str


class PassengerFlowCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    station_id: str
    timestamp: datetime
    passenger_count: int = Field(ge=0)
    avg_dwell_minutes: float = Field(default=2.5, ge=0)
    weather_code: str = Field(default="clear", min_length=3, max_length=20)
    event_flag: bool = False
    event_name: str | None = Field(default=None, max_length=80)
    source: str = Field(default="manual", max_length=32)


class PassengerFlowUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime | None = None
    passenger_count: int | None = Field(default=None, ge=0)
    avg_dwell_minutes: float | None = Field(default=None, ge=0)
    weather_code: str | None = Field(default=None, min_length=3, max_length=20)
    event_flag: bool | None = None
    event_name: str | None = Field(default=None, max_length=80)
    source: str | None = Field(default=None, max_length=32)


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    station_id: str | None = None
    origin_station_id: str | None = None
    destination_station_id: str | None = None
    target_timestamp: datetime | None = None
    horizon_hours: int = Field(default=1, ge=1, le=72)
    horizon_minutes: int | None = Field(default=None, ge=1, le=1440)
    weather_factor: float = Field(default=1.0, ge=0.5, le=3.0)
    event_factor: float = Field(default=1.0, ge=0.5, le=3.0)
    current_count: int | None = Field(default=None, ge=0)


class PredictionResponse(BaseModel):
    id: str
    station_id: str
    station_name: str
    line: str
    origin_station_name: str | None = None
    destination_station_name: str | None = None
    target_timestamp: datetime
    predicted_count: float
    baseline_count: float
    current_passengers: int | None = None
    confidence_score: float
    confidence_percentage: str | None = None
    congestion_level: str | None = None
    anomaly_score: float
    recommended_action: str
    model_version: str
    generated_at: datetime
    horizons: dict[str, float] | None = None
    st_weight: float | None = None
    ext_weight: float | None = None
    data_source: str = "PREDICTED"
    weather_condition: str | None = None
    weather_provider: str | None = None
    forecast_disclaimer: str = "Forecast — not a guaranteed passenger count."



class TrainRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    epochs: int = Field(default=24, ge=1, le=500)
    learning_rate: float = Field(default=0.001, gt=0.0, le=1.0)
    lookback_steps: int = Field(default=24, ge=1, le=168)


class TrainResponse(BaseModel):
    status: str
    model_version: str
    rmse: float
    mae: float
    message: str
