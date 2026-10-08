import pytest
import pandas as pd
from src.data.od_dataset import generate_smartcard_od_dataset
from src.training.train import train_model
from src.serving.inference import predict_flow


def test_generate_smartcard_od_dataset() -> None:
    df = generate_smartcard_od_dataset(num_days=2, stations=["ST01", "ST02", "ST03"])
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "passenger_count" in df.columns
    assert "origin_station" in df.columns
    assert "destination_station" in df.columns


def test_train_model_with_generated_dataset() -> None:
    df = generate_smartcard_od_dataset(num_days=3)
    metrics = train_model(df, save_checkpoint=True)
    assert metrics["status"] == "completed"
    assert "rmse" in metrics
    assert "mae" in metrics
    assert "mape_pct" in metrics
    assert "attention_weights" in metrics
    assert "spatial_temporal_weight" in metrics["attention_weights"]
    assert "external_context_weight" in metrics["attention_weights"]


def test_predict_flow_with_attention_weights() -> None:
    result = predict_flow(current_count=500, horizon_minutes=30, weather_factor=1.1, event_factor=1.0, is_peak_hour=True)
    assert "predicted_count" in result
    assert "horizons" in result
    assert "15m" in result["horizons"]
    assert "attention_weights" in result
    assert result["confidence_score"] > 0.0
