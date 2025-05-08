from typing import TypedDict


# TODO: use pydantic models instead

class DateTemperatureDict(TypedDict):
    date: str
    temperature: float


class DateTemperaturesDict(TypedDict):
    error_message: str | None
    temperatures: list[DateTemperatureDict] | None


class LocationInfo(TypedDict):
    lat: float | None
    lon: float | None


class WeatherForecastResponse(DateTemperaturesDict):
    location: LocationInfo


class PlaceSearchResponse(TypedDict):
    error_message: str | None
    place: str
    lat: float | None
    lon: float | None
