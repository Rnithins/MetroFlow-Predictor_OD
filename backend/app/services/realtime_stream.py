from __future__ import annotations

import random
from datetime import datetime, UTC
import numpy as np


def get_realtime_telemetry_stream(station_code: str = "DEL_RAJ") -> dict:
    """
    Simulates real-time telemetry sensor stream from smart cards, GPS train trackers,
    IoT platform weight sensors, and CCTV crowd count cameras.
    """
    now = datetime.now(UTC)
    hour = now.hour
    is_peak = hour in {8, 9, 17, 18, 19}

    base_crowd = random.randint(850, 1400) if is_peak else random.randint(250, 650)
    
    return {
        "timestamp": now.isoformat(),
        "station_code": station_code,
        "smart_card_taps_per_min": random.randint(120, 280) if is_peak else random.randint(30, 95),
        "cctv_crowd_count": base_crowd,
        "cctv_occupancy_pct": round(min(100.0, base_crowd / 12.0), 1),
        "iot_platform_sensors": {
            "platform_1_weight_load_kg": random.randint(25000, 68000),
            "platform_2_weight_load_kg": random.randint(22000, 62000),
            "ambient_temp_celsius": round(26.5 + random.uniform(-2.0, 3.5), 1),
            "air_quality_index": random.randint(85, 175),
        },
        "gps_train_tracker": {
            "incoming_train_id": f"TRN_{random.randint(101, 109)}",
            "eta_seconds": random.randint(30, 240),
            "train_occupancy_pct": random.randint(70, 98) if is_peak else random.randint(35, 65),
            "current_speed_kmh": random.randint(38, 52),
        },
        "stream_status": "ONLINE",
        "data_freshness": "REAL_TIME_<1s",
    }
