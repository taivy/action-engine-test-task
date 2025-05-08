from typing import Optional
from fastapi import FastAPI, Query, HTTPException, status

import config
from utils import get_daily_14h_temperatures, geocode_place
from schemas import PlaceSearchResponse, WeatherForecastResponse


app = FastAPI(
    title="Weather at 14:00 API",
    description="Get daily temperature data for Belgrade (or other locations) at 14:00."
)


@app.get(
    "/weather",
    summary="Get daily 14:00 temperatures. Returns forecast for "
    "Belgrade if no parameters specified",
    tags=["API"]
)
async def weather(
    lat: Optional[float] = Query(None, description="Latitude"),
    lon: Optional[float] = Query(None, description="Longitude"),
    place: Optional[str] = Query(None, description="Place name")
) -> WeatherForecastResponse:
    """
    Get daily temperature at 14:00 for Belgrade or specified location.
    - If `place` is given, it is geocoded to coordinates.
    - If `lat` and `lon` are given, they are used.
    - Otherwise, Belgrade is used by default.
    """
    response: WeatherForecastResponse = {
        "location": {},
        "temperatures": None,
        "error_message": None
    }
    if place:
        coords = await geocode_place(place)
        if not coords:
            response["error_message"] = "Place not found"
            # TODO: maybe return status_code=404
            return response
        lat, lon = coords
    # Explicitly define other cases
    elif lat is None and lon is None:
        lat, lon = config.BELGRADE_COORDINATES
    elif lat is None or lon is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Place isn't specified and one of coordinates is missing"
        )
    temps = await get_daily_14h_temperatures(lat, lon)
    temps["location"] = {"lat": lat, "lon": lon}
    return temps


@app.get("/search", summary="Search for place coordinates", tags=["API"])
async def search(
    place: str = Query(..., description="Place name to search")
) -> PlaceSearchResponse:
    """
    Search for a place by name and return its coordinates.
    """
    response: PlaceSearchResponse = {
        "error_message": None,
        "place": place,
        "lat": None,
        "lon": None
    }
    coords = await geocode_place(place)
    if not coords:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found"
        )
    response["lat"], response["lon"] = coords[0], coords[1]
    return response
