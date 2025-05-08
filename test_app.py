import pytest
from fastapi.testclient import TestClient

import config
from main import app


client = TestClient(app)

BELGRADE_LAT, BELGRADE_LON = config.BELGRADE_COORDINATES


# TODO: use pytest.parametrize to reduce number of separate test
# functions with repeated code


@pytest.mark.asyncio
async def test_weather_belgrade():
    resp = client.get("/weather")
    assert resp.status_code == 200
    data = resp.json()
    assert data["location"]["lat"] == pytest.approx(BELGRADE_LAT, abs=0.01)
    assert data["location"]["lon"] == pytest.approx(BELGRADE_LON, abs=0.01)
    assert "temperatures" in data
    assert isinstance(data["temperatures"], list)
    assert len(data["temperatures"]) > 0
    daily_record = data["temperatures"][0]
    assert daily_record["date"] is not None
    assert daily_record["temperature"] is not None
    assert isinstance(daily_record["temperature"], float)


@pytest.mark.asyncio
async def test_weather_by_coords():
    resp = client.get(f"/weather?lat={BELGRADE_LAT}&lon={BELGRADE_LON}")
    assert resp.status_code == 200
    data = resp.json()
    assert "temperatures" in data
    assert isinstance(data["temperatures"], list)
    assert len(data["temperatures"]) > 0
    daily_record = data["temperatures"][0]
    assert daily_record["date"] is not None
    assert daily_record["temperature"] is not None
    assert isinstance(daily_record["temperature"], float)


@pytest.mark.asyncio
async def test_weather_missing_coordinate():
    resp = client.get(f"/weather?lat={BELGRADE_LAT}")
    assert resp.status_code == 400
    data = resp.json()
    assert data["detail"] == "Place isn't specified and one of coordinates is missing"


@pytest.mark.asyncio
async def test_weather_by_invalid_coords():
    resp = client.get(f"/weather?lat=abc&lon=test")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_place():
    resp = client.get("/search?place=Moscow")
    assert resp.status_code == 200
    data = resp.json()
    assert "lat" in data and "lon" in data


@pytest.mark.asyncio
async def test_search_place():
    resp = client.get("/search?place=New-York")
    assert resp.status_code == 200
    data = resp.json()
    assert "lat" in data and "lon" in data


@pytest.mark.asyncio
async def test_search_place_not_found():
    resp = client.get("/search?place=asdkjfhaksjdhf")
    assert resp.status_code == 404
    data = resp.json()
    assert data["detail"] == "Place not found"
