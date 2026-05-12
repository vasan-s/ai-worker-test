"""MCP server exposing the travel knowledge base as tools.

Run standalone for stdio transport:
    python -m backend.mcp_server
"""

from mcp.server.fastmcp import FastMCP

from backend.knowledge_base import (
    PLACES,
    get_forecast,
    get_place,
    list_place_keys,
)

mcp = FastMCP("travel-knowledge")


@mcp.tool()
def list_destinations() -> list[str]:
    """List the names of all destinations available in the travel knowledge base."""
    return [PLACES[k]["city"] for k in list_place_keys()]


@mcp.tool()
def get_place_details(city: str) -> dict:
    """Look up details (attractions, season, currency, summary) for a destination city."""
    place = get_place(city)
    if place is None:
        return {"error": f"No information available for '{city}'. Try list_destinations."}
    return place


@mcp.tool()
def get_weather_forecast(city: str, travel_date: str) -> dict:
    """Return a forecast for the given city and ISO date (YYYY-MM-DD)."""
    forecast = get_forecast(city, travel_date)
    if forecast is None:
        return {"error": f"Could not produce a forecast for '{city}' on {travel_date}."}
    return forecast


if __name__ == "__main__":
    mcp.run()
