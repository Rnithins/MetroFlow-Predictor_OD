from __future__ import annotations

import pandas as pd


def clean_flow_data(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned["flow_timestamp"] = pd.to_datetime(cleaned["flow_timestamp"])
    cleaned["hour"] = cleaned["flow_timestamp"].dt.hour
    cleaned["day_of_week"] = cleaned["flow_timestamp"].dt.dayofweek
    cleaned["is_weekend"] = cleaned["day_of_week"].isin([5, 6]).astype(int)
    cleaned = cleaned.fillna(
        {
            "weather_code": "clear",
            "event_flag": False,
            "avg_dwell_minutes": 0.0,
        }
    )
    return cleaned
