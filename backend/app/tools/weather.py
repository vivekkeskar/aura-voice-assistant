import urllib.parse
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.tools.base import BaseTool, tool_registry
from app.utils.logger import logger

WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherTool(BaseTool):
    name = "get_weather"
    description = (
        "Fetch real-time weather information for a specified location. "
        "Dynamic city or region location argument MUST be provided."
    )
    parameters = {
        "type": "OBJECT",
        "properties": {
            "location": {
                "type": "STRING",
                "description": "The city or region name (e.g., 'Pune', 'Mumbai', 'Solapur', 'Delhi', 'London', 'New York').",
            }
        },
        "required": ["location"],
    }

    async def execute(self, params: Dict[str, Any], session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        location = params.get("location", "").strip()
        if not location:
            return {"error": "Location parameter is required."}

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                # 1. Geocode location to lat/lon
                encoded_loc = urllib.parse.quote(location)
                geo_url = (
                    f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_loc}&count=1&language=en&format=json"
                )
                geo_resp = await client.get(geo_url)
                geo_data = geo_resp.json()

                if not geo_data.get("results"):
                    return {"error": f"Location '{location}' not found."}

                target = geo_data["results"][0]
                lat = target["latitude"]
                lon = target["longitude"]
                resolved_name = target.get("name", location)
                country = target.get("country", "")

                # 2. Fetch current weather from Open-Meteo API
                weather_url = (
                    f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                )
                weather_resp = await client.get(weather_url)
                weather_data = weather_resp.json()

                current = weather_data.get("current_weather", {})
                temp_c = current.get("temperature")
                wind_speed = current.get("windspeed")
                weather_code = current.get("weathercode", 0)
                condition = WEATHER_CODE_MAP.get(weather_code, "Unknown")

                result = {
                    "location": f"{resolved_name}{', ' + country if country else ''}",
                    "latitude": lat,
                    "longitude": lon,
                    "temperature": f"{temp_c}°C",
                    "condition": condition,
                    "wind_speed": f"{wind_speed} km/h",
                }
                logger.info(f"Weather fetched successfully for {location} (lat={lat}, lon={lon}): {result}")
                return result
        except httpx.TimeoutException:
            logger.error(f"Weather API timeout for location: {location}")
            return {"error": f"Weather API request timed out for location '{location}'."}
        except Exception as e:
            logger.error(f"Error fetching weather for {location}: {e}")
            return {"error": f"Failed to fetch weather: {str(e)}"}


tool_registry.register(WeatherTool())
