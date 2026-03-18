import random
import os
import sqlite3
from drone import Drone
from region import Region

GRID_SIZE = 200
DB_NAME = "simulation.db"
temp_current_time = 400

class Simulation:
    def __init__(self):
        self.grid = [["empty" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.drones = {}
        self.regions = {}
        self.survivors = []
        self.conn = sqlite3.connect(DB_NAME)
        self._init_db()
        self._load_regions()
        self._load_drones()

    def _init_db(self):
        cursor = self.conn.cursor()
        # create tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regions (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                coordinates TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drones (
                drone_id TEXT PRIMARY KEY,
                region_id TEXT,
                x INTEGER,
                y INTEGER,
                battery INTEGER,
                state TEXT,
                FOREIGN KEY (region_id) REFERENCES regions(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drone_logs (
                drone_id TEXT,
                region_id TEXT,
                time TEXT,
                battery INTEGER,
                x INTEGER,
                y INTEGER,
                state TEXT
            )
        """)
        self.conn.commit()

    # load regions from db into dict on startup
    def _load_regions(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, description, coordinates FROM regions")
        for row in cursor.fetchall():
            id, name, description, coordinates = row
            self.regions[id] = Region(name, id, description, coordinates)
        print(f"Loaded {len(self.regions)} regions from database.")

    # load drones from db into dict on startup
    # allows us to reach O(1) access time for drones instead of O(n) if we were to store in a list
    def _load_drones(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT drone_id, region_id, x, y FROM drones")
        for row in cursor.fetchall():
            drone_id, region_id, x, y = row
            match_region = self.regions.get(region_id)
            if match_region:
                self.drones[drone_id] = Drone(drone_id, x, y, match_region)
        print(f"Loaded {len(self.drones)} drones from database.")

    def add_region(self, name, id, description, coordinates):
        region = Region(name, id, description, coordinates)
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO regions (id, name, description, coordinates) VALUES (?, ?, ?, ?)",
                (id, name, description, str(coordinates))
            )
            self.conn.commit()
            self.regions[id] = region
            print(f"Region '{id}' added.")
        except sqlite3.IntegrityError:
            print(f"Region '{id}' already exists.")

    def add_drone(self, drone_id, x, y, region_id: str):
        match_region = self.regions.get(region_id)
        if match_region is None:
            print(f"Region '{region_id}' not found. Drone '{drone_id}' not added.")
            return
        drone = Drone(drone_id, x, y, match_region)
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO drones (drone_id, region_id, x, y, battery, state) VALUES (?, ?, ?, ?, ?, ?)",
                (drone_id, region_id, x, y, drone.get_battery(), drone.get_state())
            )
            self.conn.commit()
            self.drones[drone_id] = drone
            print(f"Drone '{drone_id}' added.")
        except sqlite3.IntegrityError:
            print(f"Drone '{drone_id}' already exists.")

    def move_drone(self, drone_id, x, y):
        drone = self.drones.get(drone_id)
        if drone is None:
            print(f"Drone '{drone_id}' not found. Cannot move.")
            return False
        drone.move(x, y)
        # update position in db
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE drones SET x = ?, y = ? WHERE drone_id = ?",
            (drone.get_x_pos(), drone.get_y_pos(), drone_id)
        )
        self.conn.commit()
        self.log_drone_state(drone_id)
        return True

    def log_drone_state(self, drone_id):
        drone = self.drones.get(drone_id)
        if drone is None:
            return
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO drone_logs (drone_id, region_id, time, battery, x, y, state) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (drone_id, drone.region.id, temp_current_time, drone.get_battery(), drone.get_x_pos(), drone.get_y_pos(), drone.get_state())
        )
        self.conn.commit()

    def thermal_scan(self, drone_id):
        drone = self.drones.get(drone_id)
        if drone is None:
            print(f"Drone '{drone_id}' not found.")
            return False
        pos = drone.get_position()
        self.log_drone_state(drone_id)
        if pos in self.survivors:
            print(f"Survivor found at {pos}")
            self.log_drone_state(drone_id)
            return True
        return False

    def get_battery_status(self, drone_id):
        drone = self.drones.get(drone_id)
        if drone:
            return drone.get_battery()
        return None

    def place_survivors(self, count):
        for _ in range(count):
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            self.survivors.append((x, y))

    def close(self):
        self.conn.close()