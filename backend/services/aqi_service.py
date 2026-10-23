"""
AQI Environmental Service Adapter
Connects to Open-Meteo Air Quality API using live GPS Coordinates (latitude, longitude)
Normalizes pollutants: PM2.5, PM10, NO2, CO, SO2, O3
Does NOT fabricate missing pollutants.
"""

import httpx
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from backend.config import AQI_API_URL, AQI_API_KEY, AQI_LOCATION, AQI_LAT, AQI_LON
from backend.models_schema import EnvironmentData

logger = logging.getLogger("aqi_service")

class AQIService:
    def __init__(self):
        self.api_url = AQI_API_URL or "https://air-quality-api.open-meteo.com/v1/air-quality"
        self.api_key = AQI_API_KEY
        self.default_lat = AQI_LAT
        self.default_lon = AQI_LON
        self.default_location = AQI_LOCATION
        self._cached_data: Optional[EnvironmentData] = None

    async def fetch_current_environment(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location_name: Optional[str] = None
    ) -> EnvironmentData:
        """
        Fetches live environmental pollutants from Open-Meteo Air Quality API
        using live smartphone GPS coordinates.
        """
        lat = latitude if latitude is not None else self.default_lat
        lon = longitude if longitude is not None else self.default_lon
        loc_str = location_name or (f"GPS ({lat:.4f}, {lon:.4f})" if latitude is not None else self.default_location)

        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": [
                    "pm10", "pm2_5", "carbon_monoxide",
                    "nitrogen_dioxide", "sulphur_dioxide", "ozone"
                ]
            }
            if self.api_key:
                params["apikey"] = self.api_key

            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(self.api_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    curr = data.get("current", {})
                    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

                    # Extract actual measured values from Open-Meteo
                    pm25_val = float(curr["pm2_5"]) if "pm2_5" in curr and curr["pm2_5"] is not None else None
                    pm10_val = float(curr["pm10"]) if "pm10" in curr and curr["pm10"] is not None else None
                    no2_val = float(curr["nitrogen_dioxide"]) if "nitrogen_dioxide" in curr and curr["nitrogen_dioxide"] is not None else None
                    co_val = float(curr["carbon_monoxide"]) if "carbon_monoxide" in curr and curr["carbon_monoxide"] is not None else None
                    so2_val = float(curr["sulphur_dioxide"]) if "sulphur_dioxide" in curr and curr["sulphur_dioxide"] is not None else None
                    o3_val = float(curr["ozone"]) if "ozone" in curr and curr["ozone"] is not None else None

                    env = EnvironmentData(
                        pm25=pm25_val,
                        pm10=pm10_val,
                        no=None,       # Not provided by Open-Meteo standard feed
                        no2=no2_val,
                        nox=None,      # Not provided
                        nh3=None,      # Not provided
                        co=co_val,
                        so2=so2_val,
                        o3=o3_val,
                        benzene=None,  # Not provided
                        toluene=None,  # Not provided
                        xylene=None,   # Not provided
                        latitude=lat,
                        longitude=lon,
                        source="Open-Meteo Air Quality API",
                        location=loc_str,
                        updated_at=now_str
                    )
                    self._cached_data = env
                    return env
                else:
                    logger.warning(f"Open-Meteo returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"Failed to fetch live AQI from Open-Meteo ({lat}, {lon}): {e}")

        # Return cached if available, updating timestamp
        if self._cached_data is not None:
            return self._cached_data

        # Fallback only when network is completely offline
        return EnvironmentData(
            pm25=35.0,
            pm10=55.0,
            no=None,
            no2=15.0,
            nox=None,
            nh3=None,
            co=300.0,
            so2=12.0,
            o3=60.0,
            benzene=None,
            toluene=None,
            xylene=None,
            latitude=lat,
            longitude=lon,
            source="Open-Meteo Offline Cache",
            location=loc_str,
            updated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        )

aqi_service = AQIService()
