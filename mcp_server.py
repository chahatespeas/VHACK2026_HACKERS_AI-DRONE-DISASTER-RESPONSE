# mcp server from workshop 3
# https://github.com/TharunRaj7/agentic-demo

import json
import os

import requests
from fastmcp import FastMCP  # Corrected import

# setup

mcp = FastMCP("drone-agent")

DRONE_DATA_PATH = os.path.join(os.path.dirname(__file__), "environment_simulation.txt")
MOCK_API_BASE = "http://localhost:8001"

# tools

@mcp.tool()
def get_drone_scan(drone_id: str) -> str:
    """Get scan results for a specific drone."""
    try:
        resp = requests.get(f"{MOCK_API_BASE}/drones/{drone_id}", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("scan_result", "extracted information")
    except requests.ConnectionError:
        return (
            "Error: Could not connect to the drone API. "
            "Make sure it is running with: uvicorn mock_drone_api:app --port 8001"
        )
    except requests.HTTPError as exc:
        return f"Error fetching scan for drone {drone_id}: {exc}"

@mcp.tool()
def get_drone_location(drone_id: str = "") -> str:
    """Get location/status for a specific drone or all drones."""
    try:
        if drone_id:
            resp = requests.get(f"{MOCK_API_BASE}/drones/{drone_id}", timeout=5)
        else:
            resp = requests.get(f"{MOCK_API_BASE}/drones", timeout=5)
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
    except requests.ConnectionError:
        return (
            "Error: Could not connect to the drone API. "
            "Make sure it is running with: uvicorn mock_drone_api:app --port 8001"
        )
    except requests.HTTPError as exc:
        return f"Error fetching drone status: {exc}"

if __name__ == "__main__":
    mcp.run(transport="stdio")