from __future__ import annotations

from dataclasses import asdict

from src.config import ModelConfig


def predict_flow(current_count: int, horizon_minutes: int, weather_factor: float, event_factor: float, is_peak_hour: bool) -> dict:
    config = ModelConfig()
    peak_multiplier = 1.25 if is_peak_hour else 1.0
    projected = current_count * (1 + horizon_minutes / 180) * weather_factor * event_factor * peak_multiplier
    return {
        "predicted_count": round(projected, 2),
        "confidence_score": 0.88,
        "model_version": config.model_version,
        "config": asdict(config),
    }
