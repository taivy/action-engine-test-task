import httpx

from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from json.decoder import JSONDecodeError

from timezonefinder import TimezoneFinder 
from dateutil import tz

import config
from schemas import DateTemperatureDict, DateTemperaturesDict


# Simple in-memory cache (to avoid overloading yr.no; rate limiting should also
# be added for this)
weather_cache = {}


def get_place_timezone(lat: float, lon: float) -> str:
    tz_finder = TimezoneFinder()
    return tz_finder.timezone_at(lng=lon, lat=lat)


async def fetch_weather(lat: float, lon: float) -> dict:
    cache_key = f"{lat:.4f},{lon:.4f}"
    now = datetime.utcnow()
    if cache_key in weather_cache:
        cached, ts = weather_cache[cache_key]
        if (now - ts).total_seconds() < config.CACHE_TTL:
            return cached
    headers = {"User-Agent": config.USER_AGENT_FOR_REQUESTS}
    params = {"lat": lat, "lon": lon}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            config.YR_NO_API_URL,
            params=params,
            headers=headers,
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
        weather_cache[cache_key] = (data, now)
        return data


def extract_14h_temperatures(
    weather_data: dict,
    place_tz: str
) -> List[DateTemperatureDict]:
    """Extract daily temperature at 14:00 from the forecast."""
    timeseries = weather_data.get("properties", {}).get("timeseries", [])
    # YR.NO returns timestamps in UTC. We need to convert it to local 
    # timezone to correctly determine (local) 14:00
    place_tz = tz.gettz(place_tz)
    temps_by_dates: List[DateTemperatureDict] = []
    for entry in timeseries:
        # TODO: test and handle DST timezone change
        dt = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        local_dt = dt.astimezone(place_tz)
        hour = local_dt.hour
        date = local_dt.date().isoformat()
        if hour == 14:
            temp = entry["data"]["instant"]["details"].get("air_temperature")
            if temp is not None:
                temp_for_date: DateTemperatureDict = {
                    "date": date,
                    "temperature": temp
                }
                temps_by_dates.append(temp_for_date)
    return temps_by_dates


async def get_daily_14h_temperatures(lat: float, lon: float) -> DateTemperaturesDict:
    result: DateTemperaturesDict = {"error_message": None, "temperatures": None}
    api_err = None
    # TODO: handle more exception types (e.g. timeout error), use logging to store details
    try:
        api_data = await fetch_weather(lat, lon)
    except httpx.RequestError as exc:
        api_err = f"An error occurred while requesting weather forecast API."
    except httpx.HTTPStatusError as exc:
        api_err = f"Error code {exc.response.status_code} requesting weather forecast API."
    except JSONDecodeError:
        api_err = f"Error decoding JSON response from weather forecast API."
    if api_err is not None:
        result["error_message"] = api_err
        return result
    place_tz = get_place_timezone(lat, lon)
    temperatures = extract_14h_temperatures(api_data, place_tz)
    result["temperatures"] = temperatures
    return result


async def geocode_place(place: str) -> Optional[Tuple[float, float]]:
    """Find coordinates for a place name using Nominatim (OpenStreetMap)."""
    # TODO: add network/requests errors handling
    url = config.GEOCODING_API_URL
    params = {"q": place, "format": "json", "limit": 1}
    headers = {"User-Agent": config.USER_AGENT_FOR_REQUESTS}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        results = r.json()
        if len(results) > 0:
            lat = results[0].get("lat")
            lon = results[0].get("lon")
            if lat is None or lon is None:
                return None
            try:
                lat = float(lat)
                lon = float(lon)
            except ValueError:
                # TODO: log this error
                return None
            return lat, lon
    return None
