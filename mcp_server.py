# mcp server from workshop 3
# https://github.com/TharunRaj7/agentic-demo

import json
import os

import requests
from fastmcp import FastMCP  # Corrected import

# setup

mcp = FastMCP("drone-agent")

DRONE_DATA_PATH = os.path.join(os.path.dirname(__file__), "simulation.db")
MOCK_API_BASE = "http://localhost:8001"

# tools
@mcp.tool()
def add_drone(drone_id: str, x: int, y: int, region_id: str) -> str:
    """Add a new drone to the simulation."""
    try:
        resp = requests.post(
            f"{MOCK_API_BASE}/drones",
            json={"drone_id": drone_id, "x": x, "y": y, "region_id": region_id},
            timeout=5
        )
        resp.raise_for_status()
        return f"Drone {drone_id} added at ({x}, {y}) in region {region_id}."
    except requests.ConnectionError:
        return (
            "Error: Could not connect to the drone API. "
            "Make sure it is running with: uvicorn mock_drone_api:app --port 8001"
        )
    except requests.HTTPError as exc:
        return f"Error adding drone {drone_id}: {exc}"
    
@mcp.tool()
def add_region(name: str, id: str, description: str, coordinates: str) -> str:
    """Add a new region to the simulation."""
    try:
        resp = requests.post(
            f"{MOCK_API_BASE}/regions",
            json={"name": name, "id": id, "description": description, "coordinates": coordinates},
            timeout=5
        )
        resp.raise_for_status()
        return f"Region '{id}' added."
    except requests.ConnectionError:
        return (
            "Error: Could not connect to the drone API. "
            "Make sure it is running with: uvicorn mock_drone_api:app --port 8001"
        )
    except requests.HTTPError as exc:
        return f"Error adding region '{id}': {exc}"
    
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
    
@mcp.tool()
def move_drone(drone_id: str, x: int, y: int) -> str:
    """Move a specific drone to new coordinates."""
    try:
        resp = requests.post(
            f"{MOCK_API_BASE}/drones/{drone_id}/move",
            json={"x": x, "y": y},
            timeout=5
        )
        resp.raise_for_status()
        return f"Drone {drone_id} moved to ({x}, {y})."
    except requests.ConnectionError:
        return (
            "Error: Could not connect to the drone API. "
            "Make sure it is running with: uvicorn mock_drone_api:app --port 8001"
        )
    except requests.HTTPError as exc:
        return f"Error moving drone {drone_id}: {exc}"

@mcp.tool()
def get_thermal_scan(drone_id: str) -> str:
    """Perform a thermal scan with a specific drone."""
    try:
        resp = requests.post(f"{MOCK_API_BASE}/drones/{drone_id}/scan", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return f"Thermal scan result for drone {drone_id}: {data.get('survivor_found', 'unknown')}"
    except requests.ConnectionError:
        return (
            "Error: Could not connect to the drone API. "
            "Make sure it is running with: uvicorn mock_drone_api:app --port 8001"
        )
    except requests.HTTPError as exc:
        return f"Error performing thermal scan for drone {drone_id}: {exc}"
    
@mcp.tool()
def get_battery_status(drone_id: str) -> str:
    """Get battery status for a specific drone."""
    try:
        resp = requests.get(f"{MOCK_API_BASE}/drones/{drone_id}/battery", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return f"Battery status for drone {drone_id}: {data.get('battery', 'unknown')}%"
    except requests.ConnectionError:
        return (
            "Error: Could not connect to the drone API. "
            "Make sure it is running with: uvicorn mock_drone_api:app --port 8001"
        )
    except requests.HTTPError as exc:
        return f"Error fetching battery status for drone {drone_id}: {exc}"
    
@mcp.tool()
def get_all_drones(region_id: str = "") -> str:
    """Get status for all drones, optionally filtered by region."""
    try:
        url = f"{MOCK_API_BASE}/drones"
        if region_id:
            url += f"?region_id={region_id}"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
    except requests.ConnectionError:
        return (
            "Error: Could not connect to the drone API. "
            "Make sure it is running with: uvicorn mock_drone_api:app --port 8001"
        )
    except requests.HTTPError as exc:
        return f"Error fetching drones: {exc}"
    
@mcp.tool()
def get_all_regions() -> str:
    """Get a list of all regions."""
    try:
        resp = requests.get(f"{MOCK_API_BASE}/regions", timeout=5)
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
    except requests.ConnectionError:
        return (
            "Error: Could not connect to the drone API. "
            "Make sure it is running with: uvicorn mock_drone_api:app --port 8001"
        )
    except requests.HTTPError as exc:
        return f"Error fetching regions: {exc}"
    

if __name__ == "__main__":
    mcp.run(transport="stdio")