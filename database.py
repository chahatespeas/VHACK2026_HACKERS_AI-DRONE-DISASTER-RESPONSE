"""
TEMPORARY DATABASE FOR CREATING REPORTS
database.py — Local JSON file storage for Disaster Response Drone System
=========================================================================

Replaces MongoDB entirely. No installation required — just Python's built-in
json module. All data is stored in a single folder as four JSON files:

    data/
        scan_reports.json
        missions.json
        resource_logs.json
        drone_telemetry.json

Each file is a JSON array of records. The file is read into memory on every
read operation and written back on every write — safe for a single-process
app like this one.

SETUP: Nothing. No install, no service, no config.
The data/ folder is created automatically on first run.

BACKUP: Just copy the data/ folder. That's your entire database.
RESET:  Delete the data/ folder (or individual .json files) to start fresh.
VIEW:   Open any .json file in VS Code, Notepad++, or any text editor.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATA_DIR = Path(os.environ.get("DRONE_DATA_DIR", "data"))

_FILES = {
    "scan_reports":    DATA_DIR / "scan_reports.json",
    "missions":        DATA_DIR / "missions.json",
    "resource_logs":   DATA_DIR / "resource_logs.json",
    "drone_telemetry": DATA_DIR / "drone_telemetry.json",
}

# One lock per file — prevents corruption if two requests write simultaneously
_LOCKS: dict[str, threading.Lock] = {k: threading.Lock() for k in _FILES}


# ---------------------------------------------------------------------------
# Core read / write helpers
# ---------------------------------------------------------------------------

def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for path in _FILES.values():
        if not path.exists():
            path.write_text("[]", encoding="utf-8")


def _read(collection: str) -> list[dict]:
    """Read all records from a JSON file."""
    _ensure_data_dir()
    with _LOCKS[collection]:
        with open(_FILES[collection], encoding="utf-8") as fh:
            return json.load(fh)


def _write(collection: str, records: list[dict]) -> None:
    """Write all records back to a JSON file (atomic via temp file)."""
    _ensure_data_dir()
    path = _FILES[collection]
    tmp  = path.with_suffix(".tmp")
    with _LOCKS[collection]:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(records, fh, indent=2, ensure_ascii=False, default=str)
        tmp.replace(path)   # atomic rename — no partial writes


def _append(collection: str, record: dict) -> None:
    """Append one record to a JSON file."""
    _ensure_data_dir()
    path = _FILES[collection]
    tmp  = path.with_suffix(".tmp")
    with _LOCKS[collection]:
        with open(_FILES[collection], encoding="utf-8") as fh:
            records = json.load(fh)
        records.append(record)
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(records, fh, indent=2, ensure_ascii=False, default=str)
        tmp.replace(path)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def check_storage() -> tuple[bool, str]:
    """
    Verify the data directory is writable.
    Returns (True, "") on success or (False, error_message) on failure.

    Use at app startup:
        ok, msg = check_storage()
        if not ok:
            st.error(msg)
    """
    try:
        _ensure_data_dir()
        test = DATA_DIR / ".write_test"
        test.write_text("ok")
        test.unlink()
        return True, ""
    except Exception as exc:
        return False, (
            f"Cannot write to data directory '{DATA_DIR.resolve()}'.\n"
            f"Check folder permissions.\nError: {exc}"
        )


def get_data_dir() -> str:
    """Return the absolute path to the data folder (useful for UI display)."""
    return str(DATA_DIR.resolve())


# ---------------------------------------------------------------------------
# Scan reports
# ---------------------------------------------------------------------------

def upsert_scan_report(report: dict) -> None:
    """Insert or update a scan report — matched by zone_id."""
    records = _read("scan_reports")
    for i, r in enumerate(records):
        if r.get("zone_id") == report.get("zone_id"):
            records[i] = report
            _write("scan_reports", records)
            return
    _append("scan_reports", report)


def get_scan_reports(
    zone_id: str | None = None,
    hazard_type: str | None = None,
) -> list[dict]:
    records = _read("scan_reports")
    if zone_id:
        records = [r for r in records if r.get("zone_id") == zone_id.upper()]
    if hazard_type:
        records = [
            r for r in records
            if any(h.get("type") == hazard_type.lower() for h in r.get("hazards", []))
        ]
    return records


# ---------------------------------------------------------------------------
# Missions
# ---------------------------------------------------------------------------

def insert_mission(mission: dict) -> None:
    _append("missions", mission)


def update_mission_status(mission_id: str, status: str, extra: dict | None = None) -> None:
    records = _read("missions")
    for r in records:
        if r.get("mission_id") == mission_id:
            r["status"] = status
            if extra:
                r.update(extra)
            break
    _write("missions", records)


def get_missions(
    drone_id: str | None = None,
    zone_id:  str | None = None,
    status:   str | None = None,
) -> list[dict]:
    records = _read("missions")
    if drone_id:
        records = [r for r in records if r.get("drone_id") == drone_id.upper()]
    if zone_id:
        records = [r for r in records if r.get("zone_id") == zone_id.upper()]
    if status:
        records = [r for r in records if r.get("status") == status]
    # Most recent first
    return sorted(records, key=lambda r: r.get("assigned_at", ""), reverse=True)


# ---------------------------------------------------------------------------
# Resource logs
# ---------------------------------------------------------------------------

def insert_resource_log(entry: dict) -> None:
    _append("resource_logs", entry)


def get_resource_logs(
    zone_id:    str | None = None,
    entry_type: str | None = None,
) -> list[dict]:
    records = _read("resource_logs")
    if zone_id:
        records = [r for r in records if r.get("zone_id") == zone_id.upper()]
    if entry_type:
        records = [r for r in records if r.get("entry_type") == entry_type.lower()]
    return sorted(records, key=lambda r: r.get("timestamp", ""), reverse=True)


def get_resource_summary(zone_id: str | None = None) -> list[dict]:
    """Aggregate resource log totals per zone — pure Python, no DB engine needed."""
    records = get_resource_logs(zone_id=zone_id)

    totals: dict[str, dict] = {}
    for entry in records:
        z = entry.get("zone_id", "UNKNOWN")
        if z not in totals:
            totals[z] = {
                "zone_id":            z,
                "survivors_found":    0,
                "supplies_needed":    0,
                "supplies_delivered": 0,
                "hazards_confirmed":  0,
                "areas_cleared":      0,
                "log_count":          0,
            }
        et  = entry.get("entry_type", "")
        qty = entry.get("quantity", 0)
        if et == "survivors_found":    totals[z]["survivors_found"]    += qty
        elif et == "supplies_needed":  totals[z]["supplies_needed"]    += qty
        elif et == "supplies_delivered": totals[z]["supplies_delivered"] += qty
        elif et == "hazard_confirmed": totals[z]["hazards_confirmed"]  += qty
        elif et == "area_cleared":     totals[z]["areas_cleared"]      += qty
        totals[z]["log_count"] += 1

    return sorted(totals.values(), key=lambda r: r["zone_id"])


# ---------------------------------------------------------------------------
# Drone telemetry — append-only snapshots
# ---------------------------------------------------------------------------

def record_telemetry(drone: dict) -> None:
    """Save a timestamped telemetry snapshot for a drone."""
    snapshot = {**drone, "recorded_at": now_utc()}
    _append("drone_telemetry", snapshot)


def get_telemetry(drone_id: str | None = None, limit: int = 100) -> list[dict]:
    records = _read("drone_telemetry")
    if drone_id:
        records = [r for r in records if r.get("drone_id") == drone_id.upper()]
    records = sorted(records, key=lambda r: r.get("recorded_at", ""), reverse=True)
    return records[:limit]


def get_latest_telemetry_per_drone() -> list[dict]:
    """Return the single most recent snapshot for each drone."""
    records = sorted(
        _read("drone_telemetry"),
        key=lambda r: r.get("recorded_at", ""),
        reverse=True,
    )
    seen:   set[str]  = set()
    latest: list[dict] = []
    for r in records:
        did = r.get("drone_id", "")
        if did not in seen:
            seen.add(did)
            latest.append(r)
    return sorted(latest, key=lambda r: r.get("drone_id", ""))
