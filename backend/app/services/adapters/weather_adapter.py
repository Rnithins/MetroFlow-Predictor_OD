"""
Weather Data Adapter for MetroFlowNet
Supports live weather telemetry via OpenWeatherMap API with automatic Open-Meteo fallback.
Explicitly stamps data_source = 'REALTIME' or 'SIMULATED'.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class WeatherAdapter:
    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.openweathermap_api_key

    def fetch_city_weather(self, city_name: str, lat: float, lon: float) -> dict[str, Any]:
        """
        Fetches real-time weather metrics for metro station coordinates.
        Primary: OpenWeatherMap (using configured API key)
        Fallback: Open-Meteo (keyless open atmospheric API)
        """
        now = datetime.now(UTC)

        # 1. Try OpenWeatherMap if key is configured
        if self.api_key:
            try:
                url = (
                    f"https://api.openweathermap.org/data/2.5/weather?"
                    f"lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
                )
                req = urllib.request.Request(url, headers={"User-Agent": "MetroFlowNet/2.0"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.getcode() == 200:
                        data = json.loads(response.read().decode("utf-8"))
                        main = data.get("main", {})
                        weather_arr = data.get("weather", [{}])
                        weather_desc = weather_arr[0].get("description", "clear sky") if weather_arr else "clear sky"
                        rain_obj = data.get("rain", {})
                        rain_mm = float(rain_obj.get("1h", 0.0))

                        temp = float(main.get("temp", 26.0))
                        humidity = float(main.get("humidity", 50.0))

                        # Calculate flow multiplier based on monsoon or extreme heat
                        factor = 1.0
                        if rain_mm > 5.0 or "rain" in weather_desc.lower():
                            factor = 1.15  # Heavy rain increases metro demand as commuters shift away from roads
                        elif temp > 40.0:
                            factor = 1.08  # Extreme heat increases AC metro preference

                        return {
                            "city": city_name,
                            "timestamp": now.isoformat(),
                            "temperature_celsius": temp,
                            "rainfall_mm": rain_mm,
                            "humidity_pct": humidity,
                            "weather_condition": weather_desc,
                            "demand_multiplier": round(factor, 2),
                            "provider": "OpenWeatherMap",
                            "data_source": "REALTIME",
                            "is_live": True,
                        }
            except Exception as e:
                logger.warning(f"OpenWeatherMap API request failed for {city_name}: {e}. Trying Open-Meteo fallback.")

        # 2. Keyless Open-Meteo Fallback
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,weather_code"
            req = urllib.request.Request(url, headers={"User-Agent": "MetroFlowNet/2.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    curr = data.get("current", {})
                    temp = float(curr.get("temperature_2m", 25.0))
                    humidity = float(curr.get("relative_humidity_2m", 50.0))
                    rain_mm = float(curr.get("precipitation", 0.0))
                    weather_code = curr.get("weather_code", 0)

                    desc = "Clear" if weather_code == 0 else "Partly Cloudy" if weather_code < 40 else "Rain/Showers"
                    factor = 1.15 if rain_mm > 2.0 or weather_code >= 50 else 1.0

                    return {
                        "city": city_name,
                        "timestamp": now.isoformat(),
                        "temperature_celsius": temp,
                        "rainfall_mm": rain_mm,
                        "humidity_pct": humidity,
                        "weather_condition": desc,
                        "demand_multiplier": round(factor, 2),
                        "provider": "Open-Meteo",
                        "data_source": "REALTIME",
                        "is_live": True,
                    }
        except Exception as e:
            logger.warning(f"Open-Meteo API fallback failed for {city_name}: {e}.")

        # 3. Explicitly labeled simulated atmospheric baseline if network is disconnected
        return {
            "city": city_name,
            "timestamp": now.isoformat(),
            "temperature_celsius": 28.0,
            "rainfall_mm": 0.0,
            "humidity_pct": 55.0,
            "weather_condition": "Simulated Normal Weather",
            "demand_multiplier": 1.0,
            "provider": "Local Simulation Engine",
            "data_source": "SIMULATED",
            "is_live": False,
        }
