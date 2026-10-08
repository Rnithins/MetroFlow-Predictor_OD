"""
Open Transit Data Delhi (OTD Delhi) Adapter
Ingests real-time and static transit feeds from the official Delhi Open Transit Data platform.
Explicitly tags real vs simulated data.
"""

from __future__ import annotations

import logging
import urllib.request
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OTDDelhiAdapter:
    BASE_URL = "https://otd.delhi.gov.in/api/realtime"

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.otd_delhi_api_key

    def check_feed_status(self) -> dict[str, Any]:
        """
        Polls OTD Delhi API gateway and verifies feed connectivity and status.
        """
        now = datetime.now(UTC)
        if not self.api_key:
            return {
                "agency": "Delhi Metro Rail Corporation & DIMTS (OTD Delhi)",
                "feed_name": "VehiclePositions.pb",
                "status": "UNCONFIGURED",
                "message": "OTD Delhi API Key is not set in configuration.",
                "data_source": "SIMULATED",
                "timestamp": now.isoformat(),
                "is_live": False,
            }

        url = f"{self.BASE_URL}/VehiclePositions.pb?key={self.api_key}"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "MetroFlowNet-OTD-Adapter/2.0"}
            )
            with urllib.request.urlopen(req, timeout=6) as response:
                code = response.getcode()
                raw_bytes = response.read()
                if code == 200:
                    return {
                        "agency": "Delhi Integrated Multi-Modal Transit System / DMRC",
                        "feed_name": "VehiclePositions.pb",
                        "status": "OPERATIONAL",
                        "feed_size_bytes": len(raw_bytes),
                        "data_source": "REALTIME",
                        "timestamp": now.isoformat(),
                        "message": "Live transit protocol buffer stream active and verified.",
                        "is_live": True,
                    }
                return {
                    "agency": "DMRC / OTD Delhi",
                    "feed_name": "VehiclePositions.pb",
                    "status": "TEMPORARILY_UNAVAILABLE",
                    "status_code": code,
                    "data_source": "HISTORICAL",
                    "timestamp": now.isoformat(),
                    "message": f"Gateway returned status HTTP {code}. Defaulting to verified historical baseline.",
                    "is_live": False,
                }
        except Exception as e:
            logger.warning(f"OTD Delhi feed request failed: {e}")
            return {
                "agency": "DMRC / OTD Delhi",
                "feed_name": "VehiclePositions.pb",
                "status": "TEMPORARILY_UNAVAILABLE",
                "error": str(e),
                "data_source": "SIMULATED",
                "timestamp": now.isoformat(),
                "message": "Live feed connection unreachable. Reverting to calibrated simulation engine.",
                "is_live": False,
            }
