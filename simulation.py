import random
from drones import Drone

GRID_SIZE = 10

class Simulation:
    #grid creation for 10x10 disaster map
    def __init__(self):
        self.grid = [["empty" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.drones = []
        self.survivors = []
    
    #drones added to simulation class
    def add_drone(self, drone_id, x, y):
        drone = Drone(drone_id, x, y)
        self.drones.append(drone)

    #place survivors inside simulation class
    def place_survivors(self, count):
        for _ in range(count):
            x = random.randint(0, GRID_SIZE-1)
            y = random.randint(0, GRID_SIZE-1)
            self.survivors.append((x,y))
    
    #drone movement function added
    def move_drone(self, drone_id, x, y):

        for drone in self.drones:
            if drone.id == drone_id:
                drone.move(x,y)
                return True

        return False 
    
    #thermal scan to simulate finding survivors
    def thermal_scan(self, drone_id):

        for drone in self.drones:
            if drone.id == drone_id:

                pos = drone.get_position()

                if pos in self.survivors:
                    print(f"Survivor found at {pos}")
                    return True

                return False    

    #function to check drone battery
    def get_battery_status(self, drone_id):

        for drone in self.drones:
            if drone.id == drone_id:
                return drone.get_battery()

        return None 

    #return map state (ui)
    def get_state(self):

        drone_data = []

        for d in self.drones:
            drone_data.append({
                "id": d.id,
                "x": d.x,
                "y": d.y,
                "battery": d.battery
            })

        return {
            "drones": drone_data,
            "survivors": self.survivors
        }      