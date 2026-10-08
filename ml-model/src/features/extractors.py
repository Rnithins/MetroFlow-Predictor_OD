from __future__ import annotations

import math
from datetime import datetime, date
from typing import Any
import numpy as np
import pandas as pd


# Official Indian Gazetted / Public Holidays (Month, Day)
INDIAN_PUBLIC_HOLIDAYS: set[tuple[int, int]] = {
    (1, 26),   # Republic Day
    (3, 8),    # Maha Shivratri / Holi window
    (3, 25),   # Holi
    (4, 11),   # Eid-ul-Fitr
    (4, 14),   # Dr Ambedkar Jayanti
    (4, 17),   # Ram Navami
    (4, 21),   # Mahavir Jayanti
    (5, 23),   # Buddha Purnima
    (6, 17),   # Bakrid / Eid-ul-Adha
    (7, 17),   # Muharram
    (8, 15),   # Independence Day
    (8, 26),   # Janmashtami
    (9, 16),   # Milad-un-Nabi
    (10, 2),   # Mahatma Gandhi Jayanti
    (10, 12),  # Dussehra (Vijayadashami)
    (10, 31),  # Diwali (Deepavali)
    (11, 15),  # Guru Nanak Jayanti
    (12, 25),  # Christmas
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return round(2.0 * R * math.atan2(math.sqrt(a), math.sqrt(1.0 - a)), 3)


class TemporalFeatureExtractor:
    """Extracts rich calendar, commuter peak, and Indian festival temporal features."""

    @staticmethod
    def extract(timestamp: datetime | str | pd.Timestamp) -> dict[str, Any]:
        dt = pd.to_datetime(timestamp)
        hour = dt.hour
        minute = dt.minute
        dow = dt.dayofweek  # 0 = Monday, 6 = Sunday
        month = dt.month
        day = dt.day

        # Commuter Peak Hours in Indian Metros:
        # Morning peak: 08:00 - 10:30 (8.0 to 10.5)
        # Evening peak: 17:30 - 20:30 (17.5 to 20.5)
        time_decimal = hour + minute / 60.0
        is_morning_peak = 1 if (8.0 <= time_decimal <= 10.5) else 0
        is_evening_peak = 1 if (17.5 <= time_decimal <= 20.5) else 0
        is_peak = 1 if (is_morning_peak or is_evening_peak) else 0

        # Weekend flag
        is_weekend = 1 if dow in (5, 6) else 0

        # Indian gazetted holiday flag
        is_gazetted_holiday = 1 if (month, day) in INDIAN_PUBLIC_HOLIDAYS else 0

        # Cyclical temporal encoding (sin/cos for hour and day of week)
        hour_sin = math.sin(2.0 * math.pi * hour / 24.0)
        hour_cos = math.cos(2.0 * math.pi * hour / 24.0)
        dow_sin = math.sin(2.0 * math.pi * dow / 7.0)
        dow_cos = math.cos(2.0 * math.pi * dow / 7.0)

        # Seasonality (Winter=0, Summer=1, Monsoon=2, Autumn=3)
        season = 0 if month in (12, 1, 2) else 1 if month in (3, 4, 5) else 2 if month in (6, 7, 8, 9) else 3

        return {
            "hour": hour,
            "minute": minute,
            "day_of_week": dow,
            "day": day,
            "month": month,
            "season": season,
            "is_weekend": is_weekend,
            "is_peak_hour": is_peak,
            "is_morning_peak": is_morning_peak,
            "is_evening_peak": is_evening_peak,
            "is_holiday": 1 if (is_weekend or is_gazetted_holiday) else 0,
            "is_gazetted_holiday": is_gazetted_holiday,
            "hour_sin": round(hour_sin, 4),
            "hour_cos": round(hour_cos, 4),
            "dow_sin": round(dow_sin, 4),
            "dow_cos": round(dow_cos, 4),
        }


class SpatialFeatureExtractor:
    """Extracts topology, interchange connectivity, and station capacity spatial features."""

    @staticmethod
    def extract(
        origin_station: dict[str, Any],
        destination_station: dict[str, Any] | None = None,
        network_hops: int = 1,
    ) -> dict[str, Any]:
        lat1 = float(origin_station.get("latitude", 28.6139))
        lon1 = float(origin_station.get("longitude", 77.2090))
        cap1 = int(origin_station.get("baseline_capacity", 2000))
        is_ic1 = 1 if origin_station.get("is_interchange", False) else 0
        
        # Line count through station
        lines_str = str(origin_station.get("line", ""))
        line_count = len([l for l in lines_str.replace(",", "/").split("/") if l.strip()]) or 1

        if destination_station:
            lat2 = float(destination_station.get("latitude", 28.6139))
            lon2 = float(destination_station.get("longitude", 77.2090))
            cap2 = int(destination_station.get("baseline_capacity", 2000))
            is_ic2 = 1 if destination_station.get("is_interchange", False) else 0
            distance_km = haversine_km(lat1, lon1, lat2, lon2)
            same_line = 1 if any(l in str(destination_station.get("line", "")) for l in lines_str.split("/")) else 0
        else:
            cap2 = cap1
            is_ic2 = 0
            distance_km = 0.0
            same_line = 1

        # Centrality proxy: interchanges have higher degree and betweenness
        degree_centrality = round(line_count * (2.0 if is_ic1 else 1.0), 2)
        betweenness_proxy = round(math.log(max(cap1, 500)) * (1.5 if is_ic1 else 1.0), 3)

        return {
            "origin_capacity": cap1,
            "destination_capacity": cap2,
            "origin_is_interchange": is_ic1,
            "destination_is_interchange": is_ic2,
            "line_intersection_count": line_count,
            "degree_centrality": degree_centrality,
            "betweenness_centrality": betweenness_proxy,
            "haversine_distance_km": distance_km,
            "network_hops": network_hops,
            "same_line_corridor": same_line,
        }


class ContextualFeatureExtractor:
    """Extracts real-time external weather, major events, and transit disruption features."""

    @staticmethod
    def extract(
        weather_data: dict[str, Any] | None = None,
        event_flag: bool = False,
        event_name: str | None = None,
        alert_level: str = "NORMAL",
    ) -> dict[str, Any]:
        w = weather_data or {}
        temp_c = float(w.get("temperature_celsius", 28.0))
        precip_mm = float(w.get("precipitation_mm", 0.0))
        weather_code = str(w.get("weather_condition", "clear")).lower()

        # Adverse weather indicator (heavy rain or extreme heat)
        is_adverse_weather = 1 if (precip_mm > 5.0 or "rain" in weather_code or "storm" in weather_code or temp_c > 42.0) else 0

        # Special event weighting
        is_event = 1 if event_flag else 0
        event_multiplier = 1.35 if is_event else 1.0

        # Transit disruption penalty
        alert_severity = 2 if alert_level == "CRITICAL" else 1 if alert_level == "WARNING" else 0

        return {
            "temperature_celsius": temp_c,
            "precipitation_mm": precip_mm,
            "weather_condition": weather_code,
            "is_adverse_weather": is_adverse_weather,
            "event_flag": is_event,
            "event_name": event_name or "None",
            "event_multiplier": event_multiplier,
            "transit_alert_severity": alert_severity,
        }


def extract_unified_od_feature_vector(
    origin_station: dict[str, Any],
    destination_station: dict[str, Any],
    timestamp: datetime | str,
    weather_data: dict[str, Any] | None = None,
    event_flag: bool = False,
    event_name: str | None = None,
) -> dict[str, Any]:
    """Combines temporal, spatial, and contextual extractors into a unified feature dict."""
    t_feats = TemporalFeatureExtractor.extract(timestamp)
    s_feats = SpatialFeatureExtractor.extract(origin_station, destination_station)
    c_feats = ContextualFeatureExtractor.extract(weather_data, event_flag, event_name)

    return {**t_feats, **s_feats, **c_feats}
