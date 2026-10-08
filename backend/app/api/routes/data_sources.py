"""
Data Sources & External Feeds Monitoring Router
Fulfills Enterprise Requirements:
- Sections 3, 11, 28, 30: Distinct labeling of Real-time, Historical, and Simulated feeds.
- Live telemetry from Open Transit Data Delhi and OpenWeatherMap APIs.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Query

from app.services.adapters.weather_adapter import WeatherAdapter
from app.services.adapters.otd_delhi_adapter import OTDDelhiAdapter

router = APIRouter(tags=["data-sources"])


@router.get("/status")
def get_data_sources_status() -> dict[str, Any]:
    """
    Returns the real-time status, health, and provenance badges of all external feeds.
    Strictly distinguishes between REALTIME, HISTORICAL, and SIMULATED pipelines.
    """
    weather_adapter = WeatherAdapter()
    otd_adapter = OTDDelhiAdapter()

    # Poll OTD Delhi gateway
    otd_status = otd_adapter.check_feed_status()

    # Sample weather check for National Capital Region
    weather_sample = weather_adapter.fetch_city_weather("Delhi", 28.6304, 77.2177)

    return {
        "feeds": [
            {
                "feed_name": "Open Transit Data Delhi (OTD)",
                "authority": "Delhi Integrated Multi-Modal Transit System / DMRC",
                "format": "GTFS-Realtime Protocol Buffer (.pb)",
                "status": otd_status.get("status", "OPERATIONAL"),
                "data_source": otd_status.get("data_source", "REALTIME"),
                "is_live": otd_status.get("is_live", False),
                "details": otd_status.get("message"),
                "last_polled": otd_status.get("timestamp"),
            },
            {
                "feed_name": "OpenWeatherMap Atmospheric Telemetry",
                "authority": "OpenWeatherMap Global Transit Fleet Weather",
                "format": "JSON REST",
                "status": "OPERATIONAL" if weather_sample.get("is_live") else "FALLBACK_ACTIVE",
                "data_source": weather_sample.get("data_source", "REALTIME"),
                "is_live": weather_sample.get("is_live", False),
                "details": f"Active: {weather_sample.get('weather_condition')}, {weather_sample.get('temperature_celsius')}°C",
                "last_polled": weather_sample.get("timestamp"),
            },
            {
                "feed_name": "National Static GTFS Archives",
                "authority": "BMRCL Bengaluru / CMRL Chennai / MMRC Mumbai",
                "format": "GTFS Zip (routes, stops, stop_times, calendar)",
                "status": "OPERATIONAL",
                "data_source": "HISTORICAL",
                "is_live": False,
                "details": "Verified static schedule baseline topology",
                "last_polled": None,
            },
            {
                "feed_name": "Synthetic Calibrated Simulation Engine",
                "authority": "MetroFlowNet Stochastic Inflow Simulator",
                "format": "In-Memory Generator",
                "status": "STANDBY_ACTIVE",
                "data_source": "SIMULATED",
                "is_live": False,
                "details": "Active fallback for offline or non-instrumented tier-2 corridors",
                "last_polled": None,
            },
        ],
        "disclaimer": "Live data feeds are marked REALTIME. Where feeds are inaccessible, verified HISTORICAL or calibrated SIMULATED baselines are explicitly tagged.",
    }


@router.get("/weather")
def get_city_weather(
    city: str = Query(default="Delhi", description="Metro city name"),
    lat: float = Query(default=28.6304, description="Latitude coordinate"),
    lon: float = Query(default=77.2177, description="Longitude coordinate"),
) -> dict[str, Any]:
    """
    Fetches live weather metrics and transit demand flow multipliers for a specific metro city.
    """
    weather_adapter = WeatherAdapter()
    return weather_adapter.fetch_city_weather(city, lat, lon)
