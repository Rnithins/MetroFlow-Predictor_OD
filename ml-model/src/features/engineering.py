from __future__ import annotations

import numpy as np
import pandas as pd


def build_features(frame: pd.DataFrame | dict) -> pd.DataFrame:
    """
    Computes Temporal, Spatial, and Contextual features for Adaptive Feature Fusion Network (AFFN).
    """
    if isinstance(frame, dict):
        if "dataframe" in frame and isinstance(frame["dataframe"], pd.DataFrame):
            frame = frame["dataframe"]
        elif "edge_list" in frame and isinstance(frame["edge_list"], list):
            frame = pd.DataFrame(frame["edge_list"])
        else:
            frame = pd.DataFrame(frame)

    features = frame.copy()

    # 1. Temporal Features
    if "flow_timestamp" in features.columns:
        ts = pd.to_datetime(features["flow_timestamp"])
    elif "timestamp" in features.columns:
        ts = pd.to_datetime(features["timestamp"])
    elif "Time" in features.columns:
        ts = pd.to_datetime(features["Time"])
    else:
        ts = pd.Timestamp.now()
        features["timestamp"] = ts

    features["hour"] = ts.dt.hour if hasattr(ts, "dt") else 12
    features["minute"] = ts.dt.minute if hasattr(ts, "dt") else 0
    features["day_of_week"] = ts.dt.dayofweek if hasattr(ts, "dt") else 0
    features["day"] = ts.dt.day if hasattr(ts, "dt") else 15
    features["month"] = ts.dt.month if hasattr(ts, "dt") else 7
    features["is_weekend"] = features["day_of_week"].isin([5, 6]).astype(int)

    # Peak hour flag (7:30 - 10:30 and 17:00 - 20:30)
    features["is_peak_hour"] = features["hour"].isin([7, 8, 9, 10, 17, 18, 19, 20]).astype(int)

    # Season mapping
    def get_season(month: int) -> int:
        if month in [12, 1, 2]:
            return 0  # Winter
        elif month in [3, 4, 5]:
            return 1  # Summer
        elif month in [6, 7, 8, 9]:
            return 2  # Monsoon
        else:
            return 3  # Autumn

    features["season"] = features["month"].apply(get_season)

    # Holiday / Festival flags
    if "is_holiday" not in features.columns:
        features["is_holiday"] = features["day_of_week"].apply(lambda d: 1 if d == 6 else 0)
    if "festival_score" not in features.columns:
        features["festival_score"] = 0.0

    # 2. Spatial Features
    if "route_distance_km" not in features.columns:
        features["route_distance_km"] = 8.5
    if "station_degree" not in features.columns:
        features["station_degree"] = 3
    if "interchange_count" not in features.columns:
        features["interchange_count"] = 1
    if "connectivity_score" not in features.columns:
        features["connectivity_score"] = 0.75

    # 3. Contextual Features
    if "weather_code" not in features.columns:
        features["weather_code"] = "clear"
    if "rainfall_mm" not in features.columns:
        features["rainfall_mm"] = 0.0
    if "temperature_c" not in features.columns:
        features["temperature_c"] = 28.0
    if "traffic_index" not in features.columns:
        features["traffic_index"] = 50.0
    if "cricket_match_flag" not in features.columns:
        features["cricket_match_flag"] = 0
    if "concert_flag" not in features.columns:
        features["concert_flag"] = 0
    if "school_holiday_flag" not in features.columns:
        features["school_holiday_flag"] = 0

    if "weather_factor" not in features.columns:
        weather_map = {"clear": 1.0, "cloudy": 1.05, "rain": 1.20, "storm": 1.35, "fog": 1.10}
        features["weather_factor"] = features["weather_code"].map(weather_map).fillna(1.0)

    if "event_factor" not in features.columns:
        if "event_flag" in features.columns:
            features["event_factor"] = features["event_flag"].astype(int).replace({0: 1.0, 1: 1.25})
        else:
            features["event_factor"] = 1.0 + 0.15 * features["cricket_match_flag"] + 0.10 * features["concert_flag"]

    # Historical lag / rolling statistics
    if "passenger_count" in features.columns:
        features["flow_lag_1"] = features["passenger_count"].shift(1).fillna(features["passenger_count"])
        features["flow_roll_mean_3"] = features["passenger_count"].rolling(window=3, min_periods=1).mean()

    return features
