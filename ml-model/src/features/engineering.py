from __future__ import annotations

import pandas as pd


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    features = frame.copy()
    features["is_peak_hour"] = features["hour"].isin([7, 8, 9, 17, 18, 19]).astype(int)
    features["weather_factor"] = features["weather_code"].map({"clear": 1.0, "rain": 1.12, "storm": 1.2}).fillna(1.0)
    features["event_factor"] = features["event_flag"].astype(int).replace({0: 1.0, 1: 1.18})
    features["flow_lag_1"] = features["passenger_count"].shift(1).fillna(features["passenger_count"])
    features["flow_roll_mean_3"] = features["passenger_count"].rolling(window=3, min_periods=1).mean()
    return features
