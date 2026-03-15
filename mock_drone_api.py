"""
mock_drone_api.py — Drone Backend (Environment Simulation)
===========================================================

Built from environment_simulation.txt:

  REGIONS:   A, B, C, D
  SECTIONS:  A.1–A.3, B.1–B.3, C.1–C.3, D.1–D.3
  FLEETS:    F1 (Region A), F2 (Region B), F3 (Region C), F4 (Region D)
  DRONES:    4 per fleet — F1.1–F1.4, F2.1–F2.4, F3.1–F3.4, F4.1–F4.4

Simulated behaviours:
  - get_drone_scan()     → returns "extracted information" (placeholder)
  - get_drone_position() → returns "drone is in a section" (placeholder)
  - battery is randomised (0–100%) on startup
  - if battery < 20%, drone is automatically flagged as needs_charging
    and cannot be assigned missions until recharged

Run with:
    uvicorn mock_drone_api:app --port 8001
"""

from __future__ import annotations

import itertools
import random
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import database as db

app = FastAPI(title="Drone Operations API — Environment Simulation", version="2.0.0")

# ---------------------------------------------------------------------------
# Structure constants — mirrors environment_simulation.txt
# ---------------------------------------------------------------------------

REGIONS = ["A", "B", "C", "D"]

SECTIONS: dict[str, list[str]] = {
    "A": ["A.1", "A.2", "A.3"],
    "B": ["B.1", "B.2", "B.3"],
    "C": ["C.1", "C.2", "C.3"],
    "D": ["D.1", "D.2", "D.3"],
}

# Fleet → Region assignment
FLEET_REGION: dict[str, str] = {
    "F1": "A",
    "F2": "B",
    "F3": "C",
    "F4": "D",
}

# Region → Fleet (reverse lookup)
REGION_FLEET: dict[str, str] = {v: k for k, v in FLEET_REGION.items()}

# Drone IDs per fleet (4 drones each)
FLEET_DRONES: dict[str, list[str]] = {
    "F1": ["F1.1", "F1.2", "F1.3", "F1.4"],
    "F2": ["F2.1", "F2.2", "F2.3", "F2.4"],
    "F3": ["F3.1", "F3.2", "F3.3", "F3.4"],
    "F4": ["F4.1", "F4.2", "F4.3", "F4.4"],
}

# Battery threshold — below this the drone is flagged needs_charging
BATTERY_LOW_THRESHOLD = 20

# ---------------------------------------------------------------------------
# Build the fleet state on startup with randomised battery levels
# ---------------------------------------------------------------------------

def _build_drone(fleet_id: str, drone_id: str) -> dict:
    """Build one drone's initial state with a randomised battery level."""
    battery = random.randint(0, 100)
    status  = "needs_charging" if battery < BATTERY_LOW_THRESHOLD else "idle"
    return {
        "drone_id":        drone_id,
        "fleet_id":        fleet_id,
        "region":          FLEET_REGION[fleet_id],
        "status":          status,
        "current_mission": None,
        "current_section": None,
        "battery_pct":     battery,
        "position":        "at_base",
        "last_contact":    "tempfix!",
        "low_battery_flag": battery < BATTERY_LOW_THRESHOLD,
    }


# Build all drones across all fleets
DRONES: dict[str, dict] = {}
for fleet_id, drone_ids in FLEET_DRONES.items():
    for drone_id in drone_ids:
        DRONES[drone_id] = _build_drone(fleet_id, drone_id)

# ---------------------------------------------------------------------------
# Scan report placeholders — one per section (12 total)
# ---------------------------------------------------------------------------

def _build_scan_report(region: str, section: str) -> dict:
    return {
        "section_id":       section,
        "region_id":        region,
        "fleet_id":         REGION_FLEET[region],
        "last_scanned":     None,
        "scan_data":        None,       # populated by get_drone_scan()
        "drone_position":   None,       # populated by get_drone_position()
        "hazards":          [],
        "survivor_signals": 0,
        "coverage_pct":     0,
        "scan_drone":       None,
        "notes":            "Placeholder — awaiting first scan",
    }


SCAN_REPORTS: list[dict] = [
    _build_scan_report(region, section)
    for region, sections in SECTIONS.items()
    for section in sections
]

# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------

_mission_counter = itertools.count(1)
_log_counter     = itertools.count(1)

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

VALID_MISSION_TYPES = {"recon", "survivor_search", "supply_drop", "hazard_map", "relay"}
VALID_PRIORITIES    = {"low", "normal", "high", "critical"}
VALID_ENTRY_TYPES   = {
    "survivors_found", "supplies_needed", "supplies_delivered",
    "hazard_confirmed", "area_cleared",
}
AVAILABLE_STATUSES  = {"idle"}          # needs_charging and others cannot be assigned


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _all_section_ids() -> set[str]:
    return {s for sections in SECTIONS.values() for s in sections}


# ---------------------------------------------------------------------------
# Simulated drone tool functions
# (These return placeholder strings now; replace with real sensor calls later)
# ---------------------------------------------------------------------------

def get_drone_scan(drone_id: str) -> str:
    """
    Simulated scan result for a drone.
    PLACEHOLDER: returns a fixed string as per environment_simulation.txt.
    REPLACE WITH: call to your actual drone imaging / sensor SDK.
    e.g. return drone_sdk.get_scan_data(drone_id)
    """
    return "extracted information"


def get_drone_position(drone_id: str) -> str:
    """
    Simulated position result for a drone.
    PLACEHOLDER: returns a fixed string as per environment_simulation.txt.
    REPLACE WITH: call to your actual drone GPS / telemetry SDK.
    e.g. return drone_sdk.get_position(drone_id)
    """
    drone = DRONES.get(drone_id)
    if drone and drone.get("current_section"):
        return f"drone is in section {drone['current_section']}"
    return "drone is in a section"


# ---------------------------------------------------------------------------
# Startup — seed JSON files
# ---------------------------------------------------------------------------

@app.on_event("startup")
def seed_database() -> None:
    """Seed JSON files with simulation structure on first run."""
    for report in SCAN_REPORTS:
        db.upsert_scan_report(report)
    for drone in DRONES.values():
        db.record_telemetry(drone)
    print("[startup] JSON storage ready —", db.get_data_dir())
    print(f"[startup] {len(DRONES)} drones across {len(FLEET_DRONES)} fleets")
    low = sum(1 for d in DRONES.values() if d["low_battery_flag"])
    print(f"[startup] {low} drone(s) flagged low battery (<{BATTERY_LOW_THRESHOLD}%)")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class AssignMissionRequest(BaseModel):
    drone_id:     str
    section_id:   str           # e.g. "A.1", "B.3" — sections replace zones
    mission_type: str
    priority:     str = "normal"
    notes:        str = ""


class CancelMissionRequest(BaseModel):
    drone_id: str
    reason:   str = ""


class ResourceLogRequest(BaseModel):
    section_id:  str
    entry_type:  str
    quantity:    int
    description: str
    reported_by: str = "drone-auto"


class RechargeRequest(BaseModel):
    drone_id: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    ok, msg = db.check_storage()
    return {
        "status":    "ok" if ok else "degraded",
        "storage":   f"JSON files at {db.get_data_dir()}" if ok else f"error: {msg}",
        "timestamp": _now(),
    }


# ── Fleet & drone status ────────────────────────────────────────────────────

@app.get("/fleets")
def get_fleets() -> dict:
    """Return a summary of all fleets and their region assignments."""
    result = []
    for fleet_id, drone_ids in FLEET_DRONES.items():
        fleet_drones = [DRONES[d] for d in drone_ids]
        result.append({
            "fleet_id":      fleet_id,
            "region":        FLEET_REGION[fleet_id],
            "sections":      SECTIONS[FLEET_REGION[fleet_id]],
            "drone_count":   len(fleet_drones),
            "available":     sum(1 for d in fleet_drones if d["status"] == "idle"),
            "on_mission":    sum(1 for d in fleet_drones if d["status"] in {"en_route", "on_mission"}),
            "low_battery":   sum(1 for d in fleet_drones if d["low_battery_flag"]),
            "drones":        fleet_drones,
        })
    return {"fleets": result, "total_fleets": len(result)}


@app.get("/drones")
def get_all_drones(
    fleet_id:  Optional[str] = None,
    region:    Optional[str] = None,
    status:    Optional[str] = None,
) -> dict:
    """
    Return drone fleet status with optional filters.
    PLACEHOLDER: reads from in-memory DRONES dict.
    REPLACE WITH: drone_sdk.get_fleet_status()
    """
    fleet = list(DRONES.values())
    if fleet_id:
        fleet = [d for d in fleet if d["fleet_id"] == fleet_id.upper()]
    if region:
        fleet = [d for d in fleet if d["region"] == region.upper()]
    if status:
        fleet = [d for d in fleet if d["status"] == status]
    return {
        "drones":     fleet,
        "total":      len(fleet),
        "available":  sum(1 for d in fleet if d["status"] == "idle"),
        "on_mission": sum(1 for d in fleet if d["status"] in {"en_route", "on_mission"}),
        "low_battery": sum(1 for d in fleet if d["low_battery_flag"]),
        "timestamp":  _now(),
    }


@app.get("/drones/{drone_id}")
def get_drone(drone_id: str) -> dict:
    """
    Return status for one drone — includes simulated scan + position strings.
    PLACEHOLDER: reads from DRONES dict and calls simulated tool functions.
    REPLACE WITH: drone_sdk.get_drone(drone_id)
    """
    drone = DRONES.get(drone_id)
    if not drone:
        raise HTTPException(status_code=404, detail=f"Drone '{drone_id}' not found.")
    return {
        **drone,
        "scan_result":     get_drone_scan(drone_id),
        "position_result": get_drone_position(drone_id),
    }


# ── Scan reports ────────────────────────────────────────────────────────────

@app.get("/scan-reports")
def get_scan_reports(
    region_id:   Optional[str] = None,
    section_id:  Optional[str] = None,
    fleet_id:    Optional[str] = None,
) -> dict:
    """
    Return scan reports filtered by region, section, or fleet.
    Reports start empty — populated as drones scan their sections.
    """
    results = db.get_scan_reports()

    # database.py uses zone_id — remap to section_id for this simulation
    if region_id:
        results = [r for r in results if r.get("region_id") == region_id.upper()]
    if section_id:
        results = [r for r in results if r.get("section_id") == section_id.upper()]
    if fleet_id:
        results = [r for r in results if r.get("fleet_id") == fleet_id.upper()]

    return {"scan_reports": results, "count": len(results)}


# ── Missions ────────────────────────────────────────────────────────────────

@app.post("/missions")
def assign_mission(req: AssignMissionRequest) -> dict:
    """
    Assign a mission to a drone in its fleet's region.
    - Drone must be idle (not on mission and not needs_charging)
    - Section must belong to the drone's fleet region
    - Battery < 20% blocks assignment

    PLACEHOLDER: updates in-memory DRONES dict.
    REPLACE WITH: drone_sdk.dispatch(drone_id, section_id, mission_type)
    """
    drone_id   = req.drone_id
    section_id = req.section_id.upper()
    drone      = DRONES.get(drone_id)

    if not drone:
        raise HTTPException(status_code=404, detail=f"Drone '{drone_id}' not found.")

    # Battery check
    if drone["low_battery_flag"]:
        raise HTTPException(status_code=409, detail=(
            f"Drone {drone_id} battery is {drone['battery_pct']}% "
            f"(below {BATTERY_LOW_THRESHOLD}% threshold). "
            f"Recharge before assigning missions. POST /drones/{drone_id}/recharge"
        ))

    if drone["status"] not in AVAILABLE_STATUSES:
        raise HTTPException(status_code=409, detail=(
            f"Drone {drone_id} is '{drone['status']}' — "
            f"only idle drones can be assigned missions."
        ))

    if section_id not in _all_section_ids():
        raise HTTPException(status_code=404, detail=(
            f"Section '{section_id}' not found. "
            f"Valid sections: {', '.join(sorted(_all_section_ids()))}"
        ))

    # Warn if section is outside the drone's fleet region (allowed but flagged)
    drone_region    = drone["region"]
    section_region  = section_id.split(".")[0]
    cross_region    = drone_region != section_region

    if req.mission_type.lower() not in VALID_MISSION_TYPES:
        raise HTTPException(status_code=400, detail=(
            f"Invalid mission type '{req.mission_type}'. "
            f"Valid: {', '.join(sorted(VALID_MISSION_TYPES))}"
        ))
    if req.priority.lower() not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=(
            f"Invalid priority '{req.priority}'. "
            f"Valid: {', '.join(sorted(VALID_PRIORITIES))}"
        ))

    mission_id = f"MSN-{next(_mission_counter):04d}"
    mission = {
        "mission_id":     mission_id,
        "drone_id":       drone_id,
        "fleet_id":       drone["fleet_id"],
        "region":         drone_region,
        "section_id":     section_id,
        "mission_type":   req.mission_type.lower(),
        "priority":       req.priority.lower(),
        "status":         "en_route",
        "cross_region":   cross_region,
        "notes":          req.notes,
        "assigned_at":    _now(),
        # Simulated tool call results recorded at assignment time
        "scan_result":    get_drone_scan(drone_id),
        "position_result": get_drone_position(drone_id),
    }

    db.insert_mission(mission)

    # Update in-memory drone state
    drone["status"]          = "en_route"
    drone["current_mission"] = req.mission_type.lower()
    drone["current_section"] = section_id
    drone["last_contact"]    = _now()
    db.record_telemetry(drone)

    return {
        "success":      True,
        "mission_id":   mission_id,
        "cross_region": cross_region,
        "warning": (
            f"Drone {drone_id} is from region {drone_region} "
            f"but assigned to section {section_id} in region {section_region}."
            if cross_region else None
        ),
        "message": (
            f"Mission {mission_id} assigned. Drone {drone_id} "
            f"(Fleet {drone['fleet_id']}, Region {drone_region}) "
            f"dispatched to section {section_id} for '{req.mission_type}' "
            f"(priority: {req.priority})."
        ),
        "mission": mission,
    }


@app.post("/missions/cancel")
def cancel_mission(req: CancelMissionRequest) -> dict:
    """
    Cancel an active mission and return drone to idle.
    PLACEHOLDER: updates in-memory DRONES dict.
    REPLACE WITH: drone_sdk.return_to_base(drone_id)
    """
    drone_id = req.drone_id
    drone    = DRONES.get(drone_id)

    if not drone:
        raise HTTPException(status_code=404, detail=f"Drone '{drone_id}' not found.")
    if drone["status"] not in {"on_mission", "en_route"}:
        raise HTTPException(status_code=409, detail=(
            f"Drone {drone_id} has no active mission "
            f"(current status: '{drone['status']}')."
        ))

    prev_mission = drone.get("current_mission", "unknown")
    prev_section = drone.get("current_section", "unknown")

    for m in db.get_missions(drone_id=drone_id, status="en_route"):
        db.update_mission_status(m["mission_id"], "cancelled", {
            "cancel_reason": req.reason,
            "cancelled_at":  _now(),
        })

    drone["status"]          = "idle"
    drone["current_mission"] = None
    drone["current_section"] = None
    drone["last_contact"]    = _now()
    db.record_telemetry(drone)

    return {
        "success": True,
        "message": (
            f"Drone {drone_id} recalled from section {prev_section}. "
            f"Mission '{prev_mission}' cancelled. Status: idle."
        ),
        "reason": req.reason or "No reason provided",
    }


@app.get("/missions")
def list_missions(
    drone_id:   Optional[str] = None,
    fleet_id:   Optional[str] = None,
    section_id: Optional[str] = None,
    status:     Optional[str] = None,
) -> dict:
    """Return mission history from missions.json with optional filters."""
    results = db.get_missions(drone_id=drone_id, status=status)
    if fleet_id:
        results = [r for r in results if r.get("fleet_id") == fleet_id.upper()]
    if section_id:
        results = [r for r in results if r.get("section_id") == section_id.upper()]
    return {"missions": results, "count": len(results)}


# ── Battery management ──────────────────────────────────────────────────────

@app.post("/drones/{drone_id}/recharge")
def recharge_drone(drone_id: str) -> dict:
    """
    Simulate recharging a drone to 100%.
    PLACEHOLDER: instantly sets battery to 100%.
    REPLACE WITH: drone_sdk.initiate_charge(drone_id) and poll until ready.
    """
    drone = DRONES.get(drone_id)
    if not drone:
        raise HTTPException(status_code=404, detail=f"Drone '{drone_id}' not found.")
    if drone["status"] in {"en_route", "on_mission"}:
        raise HTTPException(status_code=409, detail=(
            f"Drone {drone_id} is on a mission. Cancel mission before recharging."
        ))

    drone["battery_pct"]     = 100
    drone["low_battery_flag"] = False
    drone["status"]          = "idle"
    drone["last_contact"]    = _now()
    db.record_telemetry(drone)

    return {
        "success":     True,
        "drone_id":    drone_id,
        "battery_pct": 100,
        "status":      "idle",
        "message":     f"Drone {drone_id} recharged to 100%. Ready for missions.",
    }


@app.get("/drones/low-battery")
def get_low_battery_drones() -> dict:
    """Return all drones with battery below the low threshold."""
    low = [d for d in DRONES.values() if d["low_battery_flag"]]
    return {
        "low_battery_drones": low,
        "count":              len(low),
        "threshold_pct":      BATTERY_LOW_THRESHOLD,
    }


# ── Resource logs ───────────────────────────────────────────────────────────

@app.post("/resource-log")
def log_resource(req: ResourceLogRequest) -> dict:
    """Log a scan finding to resource_logs.json."""
    section_id = req.section_id.upper()
    if section_id not in _all_section_ids():
        raise HTTPException(status_code=404, detail=(
            f"Section '{section_id}' not found. "
            f"Valid: {', '.join(sorted(_all_section_ids()))}"
        ))
    if req.entry_type.lower() not in VALID_ENTRY_TYPES:
        raise HTTPException(status_code=400, detail=(
            f"Invalid entry type. Valid: {', '.join(sorted(VALID_ENTRY_TYPES))}"
        ))

    log_id = f"LOG-{next(_log_counter):04d}"
    entry  = {
        "log_id":      log_id,
        "section_id":  section_id,
        "region_id":   section_id.split(".")[0],
        "entry_type":  req.entry_type.lower(),
        "quantity":    req.quantity,
        "description": req.description,
        "reported_by": req.reported_by,
        "timestamp":   _now(),
    }
    db.insert_resource_log(entry)
    return {"success": True, "log_id": log_id, "entry": entry}


@app.get("/resource-summary")
def resource_summary(
    section_id: Optional[str] = None,
    region_id:  Optional[str] = None,
) -> dict:
    """Return aggregated resource totals from resource_logs.json."""
    logs = db.get_resource_logs()
    if section_id:
        logs = [l for l in logs if l.get("section_id") == section_id.upper()]
    if region_id:
        logs = [l for l in logs if l.get("region_id") == region_id.upper()]

    # Aggregate manually (database.py aggregates by zone_id;
    # here we aggregate by section_id instead)
    totals: dict[str, dict] = {}
    for entry in logs:
        sid = entry.get("section_id", "UNKNOWN")
        if sid not in totals:
            totals[sid] = {
                "section_id":         sid,
                "region_id":          sid.split(".")[0] if "." in sid else sid,
                "survivors_found":    0,
                "supplies_needed":    0,
                "supplies_delivered": 0,
                "hazards_confirmed":  0,
                "areas_cleared":      0,
                "log_count":          0,
            }
        et  = entry.get("entry_type", "")
        qty = entry.get("quantity", 0)
        if et == "survivors_found":      totals[sid]["survivors_found"]    += qty
        elif et == "supplies_needed":    totals[sid]["supplies_needed"]    += qty
        elif et == "supplies_delivered": totals[sid]["supplies_delivered"] += qty
        elif et == "hazard_confirmed":   totals[sid]["hazards_confirmed"]  += qty
        elif et == "area_cleared":       totals[sid]["areas_cleared"]      += qty
        totals[sid]["log_count"] += 1

    summary = sorted(totals.values(), key=lambda r: r["section_id"])
    return {
        "summary":                  summary,
        "total_sections_with_logs": len(summary),
        "total_survivors_found":    sum(s["survivors_found"]    for s in summary),
        "total_supplies_needed":    sum(s["supplies_needed"]    for s in summary),
        "total_supplies_delivered": sum(s["supplies_delivered"] for s in summary),
    }
