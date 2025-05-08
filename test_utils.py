import pytest

import config
from utils import (
    get_daily_14h_temperatures,
    geocode_place,
    get_place_timezone
)


# TODO: use mocks instead of real external API calls
# Tests using external API calls can be present, but should run rarely
# (e.g. only before pushing to the release branch)


@pytest.mark.asyncio
async def test_get_daily_14h_temperatures_belgrade():
    lat, lon = config.BELGRADE_COORDINATES
    res = await get_daily_14h_temperatures(lat, lon)
    assert "temperatures" in res
    assert res["error_message"] is None
    temps = res["temperatures"]
    assert len(temps) > 0
    daily_record = temps[0]
    # TODO: test that it's a valid date, not just "is not None"
    # (e.g. try to parse date by datetime.strptime)
    assert daily_record["date"] is not None
    assert daily_record["temperature"] is not None
    assert isinstance(daily_record["temperature"], float)


@pytest.mark.asyncio
async def test_get_daily_14h_temperatures_incorrect_coordinates():
    lat, lon = 1000000, 100000
    res = await get_daily_14h_temperatures(lat, lon)
    assert "error_message" in res
    assert "temperatures" in res
    assert res["error_message"] == "Error code 400 requesting weather forecast API."
    assert res["temperatures"] is None


@pytest.mark.asyncio
async def test_get_place_by_coordinates():
    res = await geocode_place("New-York")
    assert len(res) == 2
    assert res == (40.7127281, -74.0060152)


def test_get_place_timezone():
    belgrade_lat, belgrade_lon = config.BELGRADE_COORDINATES
    assert get_place_timezone(belgrade_lat, belgrade_lon) == "Europe/Belgrade"
    # New York
    assert get_place_timezone(40.7127281, -74.0060152) == "America/New_York"
    # Denpasar
    assert get_place_timezone(-8.6524973, 115.2191175) == "Asia/Makassar"


# TODO: tests for correct timezones handling, including DST (use mocked API response
# and test if get_daily_14h_temperatures is correct for 14th hour)
