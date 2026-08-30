import pytest

from app.tools.weather import WeatherTool


@pytest.mark.asyncio
async def test_weather_tool_valid_location():
    tool = WeatherTool()
    result = await tool.execute({"location": "Pune"})
    assert "error" not in result
    assert "Pune" in result.get("location", "")
    assert "temperature" in result
    assert "condition" in result


@pytest.mark.asyncio
async def test_weather_tool_missing_location():
    tool = WeatherTool()
    result = await tool.execute({"location": ""})
    assert "error" in result


@pytest.mark.asyncio
async def test_weather_tool_distinct_locations():
    tool = WeatherTool()
    cities = ["Pune", "Mumbai", "Solapur", "Delhi", "London"]
    coords = []

    for city in cities:
        res = await tool.execute({"location": city})
        assert "error" not in res
        assert city.lower() in res.get("location", "").lower()
        coords.append((res.get("latitude"), res.get("longitude")))

    # Verify Pune != Mumbai != Solapur != Delhi != London
    assert len(set(coords)) == len(cities)
