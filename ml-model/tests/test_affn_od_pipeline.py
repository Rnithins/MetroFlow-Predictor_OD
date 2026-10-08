from __future__ import annotations

import pytest
import torch
import pandas as pd

from src.data.od_matrix_pipeline import process_raw_tap_logs, generate_sample_tap_logs
from src.features.engineering import build_features
from src.models.hybrid_model import AdaptiveFeatureFusionNetwork
from src.serving.inference import predict_flow
from src.training.train import train_model


def test_od_matrix_pipeline():
    sample_df = generate_sample_tap_logs(num_records=150)
    matrix_df = process_raw_tap_logs(sample_df, time_interval="15m")
    assert not matrix_df.empty
    assert "Origin" in matrix_df.columns
    assert "Destination" in matrix_df.columns
    assert "Passenger_Count" in matrix_df.columns
    assert "Avg_Travel_Minutes" in matrix_df.columns


def test_feature_engineering():
    df = generate_sample_tap_logs(num_records=50)
    matrix_df = process_raw_tap_logs(df, time_interval="15m")
    features_df = build_features(matrix_df)
    
    assert "hour" in features_df.columns
    assert "minute" in features_df.columns
    assert "is_weekend" in features_df.columns
    assert "is_peak_hour" in features_df.columns
    assert "season" in features_df.columns
    assert "weather_factor" in features_df.columns


def test_affn_model_forward():
    model = AdaptiveFeatureFusionNetwork(input_size=8, hidden_size=32, graph_hidden_size=16, output_size=5)
    seq = torch.randn(4, 12, 8)
    graph = torch.randn(4, 8)
    ext = torch.randn(4, 8)

    out, weights = model.forward_with_weights(seq, graph, ext)
    assert out.shape == (4, 5)
    assert weights.shape == (4, 2)
    # Sum of softmax attention weights should equal 1
    torch.testing.assert_close(weights.sum(dim=1), torch.ones(4))


def test_predict_flow_inference():
    res = predict_flow(
        current_count=1240,
        horizon_minutes=15,
        weather_factor=1.1,
        event_factor=1.2,
        is_peak_hour=True,
        origin_station="Rajiv Chowk",
        destination_station="Noida Sector 62"
    )
    assert res["origin_station"] == "Rajiv Chowk"
    assert res["destination_station"] == "Noida Sector 62"
    assert res["current_passengers"] == 1240
    assert "predicted_count" in res
    assert "horizons" in res
    assert "15m" in res["horizons"]
    assert "congestion_level" in res
    assert "attention_weights" in res


def test_training_pipeline():
    result = train_model(save_checkpoint=False, patience=3)
    assert result["status"] == "completed"
    assert "rmse" in result
    assert "mae" in result
    assert "r2_score" in result
    assert "attention_weights" in result
