from __future__ import annotations

from datetime import UTC, timedelta

from pymongo.database import Database

from app.core.security import get_password_hash
from app.services.documents import new_id, utc_now


def ensure_indexes(database: Database) -> None:
    database.users.create_index("email", unique=True)
    database.stations.create_index("code", unique=True)
    database.passenger_flows.create_index([("station_id", 1), ("timestamp", -1)])
    database.predictions.create_index([("station_id", 1), ("target_timestamp", -1)])


def _sample_stations() -> list[dict]:
    return [
        {
            "_id": new_id(),
            "code": "CEN",
            "name": "Central Square",
            "line": "Blue",
            "zone": "A",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "baseline_capacity": 820,
            "is_interchange": True,
        },
        {
            "_id": new_id(),
            "code": "RVR",
            "name": "Riverfront",
            "line": "Blue",
            "zone": "A",
            "latitude": 12.9812,
            "longitude": 77.6044,
            "baseline_capacity": 640,
            "is_interchange": False,
        },
        {
            "_id": new_id(),
            "code": "STH",
            "name": "South Hub",
            "line": "Green",
            "zone": "B",
            "latitude": 12.9516,
            "longitude": 77.5846,
            "baseline_capacity": 780,
            "is_interchange": True,
        },
        {
            "_id": new_id(),
            "code": "TEC",
            "name": "Tech Park",
            "line": "Purple",
            "zone": "B",
            "latitude": 12.9942,
            "longitude": 77.6526,
            "baseline_capacity": 710,
            "is_interchange": False,
        },
        {
            "_id": new_id(),
            "code": "AIR",
            "name": "Airport Link",
            "line": "Gold",
            "zone": "C",
            "latitude": 13.0116,
            "longitude": 77.6246,
            "baseline_capacity": 520,
            "is_interchange": False,
        },
        {
            "_id": new_id(),
            "code": "UNI",
            "name": "University Gate",
            "line": "Green",
            "zone": "B",
            "latitude": 12.9341,
            "longitude": 77.6128,
            "baseline_capacity": 590,
            "is_interchange": False,
        },
    ]


def _weather_for(hour_offset: int, station_index: int) -> str:
    if (hour_offset + station_index) % 19 == 0:
        return "rain"
    if (hour_offset + station_index) % 7 == 0:
        return "cloudy"
    return "clear"


def seed_database(database: Database) -> None:
    if database.users.count_documents({}) > 0:
        return

    now = utc_now().astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    stations = _sample_stations()

    users = [
        {
            "_id": new_id(),
            "email": "admin@metroflow.ai",
            "full_name": "Metro Admin",
            "password_hash": get_password_hash("admin12345"),
            "role": "admin",
            "is_active": True,
            "job_title": "Operations Director",
            "organization": "MetroFlow Transit",
            "commute_line": "Blue",
            "theme_preference": "system",
            "created_at": now,
            "updated_at": now,
        },
        {
            "_id": new_id(),
            "email": "user@metroflow.ai",
            "full_name": "Transit Analyst",
            "password_hash": get_password_hash("user12345"),
            "role": "user",
            "is_active": True,
            "job_title": "Demand Analyst",
            "organization": "MetroFlow Transit",
            "commute_line": "Green",
            "theme_preference": "system",
            "created_at": now,
            "updated_at": now,
        },
    ]

    flows: list[dict] = []
    start = (now - timedelta(days=13)).replace(hour=0)
    for day_offset in range(14):
        day_start = start + timedelta(days=day_offset)
        weekend_factor = 0.82 if day_start.weekday() >= 5 else 1.0

        for hour in range(24):
            timestamp = day_start + timedelta(hours=hour)
            peak_factor = 1.75 if hour in {8, 9, 18, 19} else 1.3 if hour in {7, 10, 17, 20} else 0.58 if hour < 5 else 1.0

            for index, station in enumerate(stations):
                weather_code = _weather_for(day_offset * 24 + hour, index)
                weather_factor = 1.12 if weather_code == "rain" else 1.03 if weather_code == "cloudy" else 1.0
                event_flag = station["code"] in {"CEN", "TEC"} and day_offset % 5 == 0 and hour in {18, 19, 20}
                event_multiplier = 1.24 if event_flag else 1.0
                daily_variation = 0.93 + ((day_offset + index) % 5) * 0.03
                base = station["baseline_capacity"] * 0.34
                passenger_count = int(base * peak_factor * weekend_factor * weather_factor * event_multiplier * daily_variation)
                passenger_count = max(passenger_count, 25 + index * 8)

                flows.append(
                    {
                        "_id": new_id(),
                        "station_id": station["_id"],
                        "timestamp": timestamp,
                        "passenger_count": passenger_count,
                        "avg_dwell_minutes": round(2.4 + (peak_factor - 1) * 1.2 + index * 0.16, 2),
                        "weather_code": weather_code,
                        "event_flag": event_flag,
                        "event_name": "Stadium event" if event_flag else None,
                        "source": "seed",
                    }
                )

    latest_flow_per_station = {flow["station_id"]: flow for flow in flows}
    predictions = [
        {
            "_id": new_id(),
            "station_id": station["_id"],
            "target_timestamp": latest_flow_per_station[station["_id"]]["timestamp"] + timedelta(hours=1),
            "predicted_count": round(latest_flow_per_station[station["_id"]]["passenger_count"] * 1.08, 2),
            "baseline_count": round(latest_flow_per_station[station["_id"]]["passenger_count"] * 0.98, 2),
            "confidence_score": 0.87,
            "anomaly_score": 0.16,
            "recommended_action": "Monitor platform density and keep one standby train available.",
            "model_version": "metroflow-baseline-regression-v2",
            "generated_at": now,
            "created_by": "system",
        }
        for station in stations[:3]
    ]

    database.users.insert_many(users)
    database.stations.insert_many(stations)
    database.passenger_flows.insert_many(flows)
    database.predictions.insert_many(predictions)
