# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from simulation import Simulation
from typing import Optional

app = FastAPI(title="Drone Simulation API", version="1.0.0")
sim = Simulation()  # one shared simulation instance

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class AddRegionRequest(BaseModel):
    name: str
    id: str
    description: str
    coordinates: str

class AddDroneRequest(BaseModel):
    drone_id: str
    x: int
    y: int
    region_id: str

class MoveDroneRequest(BaseModel):
    x: int
    y: int

class PlaceSurvivorsRequest(BaseModel):
    count: int

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Regions ─────────────────────────────────────────────────────────────────

@app.post("/regions")
def add_region(req: AddRegionRequest):
    sim.add_region(req.name, req.id, req.description, req.coordinates)
    return {"success": True, "message": f"Region '{req.id}' added."}

@app.get("/regions")
def get_regions():
    return {
        "regions": [
            {"id": r.id, "name": r.name, "description": r.description}
            for r in sim.regions.values()
        ],
        "total": len(sim.regions)
    }


# ── Drones ───────────────────────────────────────────────────────────────────

@app.post("/drones")
def add_drone(req: AddDroneRequest):
    sim.add_drone(req.drone_id, req.x, req.y, req.region_id)
    return {"success": True, "message": f"Drone '{req.drone_id}' added."}

@app.get("/drones")
def get_drones(region_id: Optional[str] = None):
    drones = list(sim.drones.values())
    if region_id:
        drones = [d for d in drones if d.region.id == region_id]
    return {
        "drones": [
            {
                "id": d.id,
                "x": d.get_x_pos(),
                "y": d.get_y_pos(),
                "battery": d.get_battery(),
                "state": d.get_state(),
                "region": d.region.id
            }
            for d in drones
        ],
        "total": len(drones)
    }

@app.get("/drones/{drone_id}")
def get_drone(drone_id: str):
    drone = sim.drones.get(drone_id)
    if drone is None:
        raise HTTPException(status_code=404, detail=f"Drone '{drone_id}' not found.")
    return {
        "id": drone.id,
        "x": drone.get_x_pos(),
        "y": drone.get_y_pos(),
        "battery": drone.get_battery(),
        "state": drone.get_state(),
        "region": drone.region.id
    }

@app.post("/drones/{drone_id}/move")
def move_drone(drone_id: str, req: MoveDroneRequest):
    success = sim.move_drone(drone_id, req.x, req.y)
    if not success:
        raise HTTPException(status_code=404, detail=f"Drone '{drone_id}' not found.")
    return {"success": True, "message": f"Drone '{drone_id}' moved to ({req.x}, {req.y})."}

@app.post("/drones/{drone_id}/scan")
def thermal_scan(drone_id: str):
    drone = sim.drones.get(drone_id)
    if drone is None:
        raise HTTPException(status_code=404, detail=f"Drone '{drone_id}' not found.")
    found = sim.thermal_scan(drone_id)
    return {
        "success": True,
        "survivor_found": found,
        "position": drone.get_position()
    }

@app.get("/drones/{drone_id}/battery")
def get_battery(drone_id: str):
    battery = sim.get_battery_status(drone_id)
    if battery is None:
        raise HTTPException(status_code=404, detail=f"Drone '{drone_id}' not found.")
    return {"drone_id": drone_id, "battery": battery}


# ── Survivors ────────────────────────────────────────────────────────────────

@app.post("/survivors/place")
def place_survivors(req: PlaceSurvivorsRequest):
    sim.place_survivors(req.count)
    return {"success": True, "total_survivors": len(sim.survivors)}

@app.get("/survivors")
def get_survivors():
    return {"survivors": sim.survivors, "count": len(sim.survivors)}


# ── Shutdown ─────────────────────────────────────────────────────────────────

@app.on_event("shutdown")
def shutdown():
    sim.close()