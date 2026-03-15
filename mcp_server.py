# mcp server from workshop 3
#  https://github.com/TharunRaj7/agentic-demo

import json
import os

import requests
from mcp.server.fastmcp import FastMCP

# setup

mcp = FastMCP("drone-agent")

DRONE_DATA_PATH = os.path.join(os.path.dirname(__file__), "environment_simulation.txt")
MOCK_API_BASE = "https://localhost:8000"

# tools

@mcp.tool()
def get_drone_scan(query: str) -> str:
    with open(DRONE_DATA_PATH, encoding="utf-8") as fh:
        return fh.head()
    
@mcp.tool()
def get_drone_location(query: str) -> str:
    with open(DRONE_DATA_PATH, encoding="utf-8") as fh:
        return fh.head()
    
def get_drone_information(drone_sect: str, drone_fleet: str) -> str:
    payload: dict 
    {
        "drone_sect": drone_sect,
        "drone_fleet": drone_fleet
    }
    try:
        resp = requests.post(f"{MOCK_API_BASE}/book-room", json=payload, timeout=5)
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
    except requests.ConnectionError:
        return (
            "Error: Could not connect to the mock API. "
            "Make sure it is running with: uvicorn mock_api:app --port 8000"
        )
    except requests.HTTPError as exc:
        try:
            detail = exc.response.json().get("detail", str(exc))
        except Exception:
            detail = str(exc)
        return f"Booking failed: {detail}"
    
if __name__ == "__main__":
    mcp.run(transport="stdio")