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
    model_config = ConfigDict(extra="forbid")

    station_id: str
    target_timestamp: datetime | None = None
    horizon_hours: int = Field(default=1, ge=1, le=72)
    weather_factor: float = Field(default=1.0, ge=0.6, le=1.7)
    event_factor: float = Field(default=1.0, ge=0.7, le=2.2)
    current_count: int | None = Field(default=None, ge=0)


class PredictionResponse(BaseModel):
    id: str
    station_id: str
    station_name: str
    line: str
    target_timestamp: datetime
    predicted_count: float
    baseline_count: float
    confidence_score: float
    anomaly_score: float
    recommended_action: str
    model_version: str
    generated_at: datetime


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
