import pandas as pd

from src.training.train import train_model


def test_train_model_returns_metrics() -> None:
    frame = pd.DataFrame(
        [
            {
                "flow_timestamp": "2026-03-24T08:00:00",
                "passenger_count": 180,
                "avg_dwell_minutes": 3.2,
                "weather_code": "clear",
                "event_flag": False,
            },
            {
                "flow_timestamp": "2026-03-24T09:00:00",
                "passenger_count": 220,
                "avg_dwell_minutes": 4.0,
                "weather_code": "rain",
                "event_flag": True,
            },
        ]
    )
    result = train_model(frame)
    assert result["status"] == "completed"
    assert "rmse" in result
    assert "mae" in result
