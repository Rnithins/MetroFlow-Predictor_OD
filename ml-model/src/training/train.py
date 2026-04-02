from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error
from torch import nn
from torch.optim import Adam

from src.config import ModelConfig
from src.data.preprocessing import clean_flow_data
from src.features.engineering import build_features
from src.models.hybrid_model import HybridLSTMGNN


def train_model(frame: pd.DataFrame, config: ModelConfig | None = None) -> dict:
    cfg = config or ModelConfig()
    prepared = build_features(clean_flow_data(frame))
    feature_cols = [
        "passenger_count",
        "avg_dwell_minutes",
        "hour",
        "day_of_week",
        "is_weekend",
        "is_peak_hour",
        "weather_factor",
        "event_factor",
    ]

    features = torch.tensor(prepared[feature_cols].values, dtype=torch.float32)
    targets = torch.tensor(prepared["passenger_count"].values, dtype=torch.float32).unsqueeze(1)

    sequence_features = features.unsqueeze(0)
    graph_features = features.mean(dim=0, keepdim=True)

    model = HybridLSTMGNN(
        input_size=cfg.input_size,
        hidden_size=cfg.hidden_size,
        graph_hidden_size=cfg.graph_hidden_size,
        output_size=cfg.output_size,
    )
    optimizer = Adam(model.parameters(), lr=cfg.learning_rate)
    criterion = nn.MSELoss()

    for _ in range(cfg.epochs):
        optimizer.zero_grad()
        predictions = model(sequence_features, graph_features)
        loss = criterion(predictions.repeat(targets.size(0), 1), targets)
        loss.backward()
        optimizer.step()

    predicted = model(sequence_features, graph_features).detach().numpy().repeat(targets.size(0))
    actual = targets.squeeze(1).numpy()

    return {
        "config": asdict(cfg),
        "rmse": float(mean_squared_error(actual, predicted) ** 0.5),
        "mae": float(mean_absolute_error(actual, predicted)),
        "status": "completed",
    }
