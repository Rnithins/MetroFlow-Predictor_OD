from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
import pandas as pd


def generate_smartcard_od_dataset(
    num_days: int = 14,
    stations: list[str] | None = None,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates realistic smart-card Origin-Destination passenger flow time-series data.
    """
    random.seed(seed)
    if not stations:
        stations = ["ST01", "ST02", "ST03", "ST04", "ST05", "ST06", "ST07", "ST08"]

    records = []
    start_date = datetime(2026, 1, 1, 6, 0, 0)

    for day in range(num_days):
        current_day = start_date + timedelta(days=day)
        day_of_week = current_day.weekday()
        is_weekend = 1 if day_of_week in [5, 6] else 0
        
        # Weather & Event randomness per day
        weather_factor = random.choice([0.9, 1.0, 1.0, 1.15, 1.25])  # Rain/Storm increases metro ridership
        event_factor = 1.35 if (day % 5 == 0) else (1.0 if not is_weekend else 1.15)

        for hour in range(6, 23):  # Operating hours 6 AM to 11 PM
            is_peak = 1 if (7 <= hour <= 10 or 17 <= hour <= 20) and not is_weekend else 0
            time_factor = 2.4 if is_peak else (0.6 if is_weekend else 1.0)
            
            timestamp = current_day.replace(hour=hour, minute=0)

            for origin in stations:
                for destination in stations:
                    if origin == destination:
                        continue
                    
                    # Distance/hop heuristic
                    orig_idx = int(origin.replace("ST", ""))
                    dest_idx = int(destination.replace("ST", ""))
                    dist_hops = abs(orig_idx - dest_idx)

                    # Base flow model
                    base_flow = (50.0 / (dist_hops ** 0.5)) * time_factor * weather_factor * event_factor
                    passenger_count = int(max(5, base_flow + random.gauss(0, 8)))
                    avg_dwell = round(random.uniform(1.8, 3.5), 2)

                    records.append({
                        "timestamp": timestamp,
                        "origin_station": origin,
                        "destination_station": destination,
                        "passenger_count": passenger_count,
                        "avg_dwell_minutes": avg_dwell,
                        "hour": hour,
                        "day_of_week": day_of_week,
                        "is_weekend": is_weekend,
                        "is_peak_hour": is_peak,
                        "weather_factor": weather_factor,
                        "event_factor": event_factor,
                    })

    df = pd.DataFrame(records)
    return df
