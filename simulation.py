import random
import os 
from drones import Drone

GRID_SIZE = 10

directory_name = "drone_data"
temp_current_time = "0400"
temp_current_battery = 100

class Simulation:
    #grid creation for 10x10 disaster map
    def __init__(self):
        self.grid = [["empty" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.drones = []
        self.survivors = []
    
    #drones added to simulation class
    def add_drone(self, drone_id, x, y):
        drone = Drone(drone_id, x, y) # add battery param, figure out how to update battery based on movement and scanning
        # substitute for storing drone data

        try:
            os.mkdir(directory_name)
            print(f"Directory '{directory_name}' created.")
        except FileExistsError:
            print(f"Directory '{directory_name}' already exists.")
        except PermissionError:
            print(f"Permission denied: Unable to create directory '{directory_name}'.")
        except Exception as e:
            print(f"An error occurred while creating directory '{directory_name}': {e}")
        
        try:
            with open(f"{directory_name}/{drone_id}", "x") as f:
                f.write(f"drone_id,temp_current_time,temp_current_battery,current_x_pos,current_y_pos,\n,{drone_id},{temp_current_time},{temp_current_battery},{drone.get_x_pos()},{drone.get_y_pos()}\n")
        except FileExistsError:
            print(f"Drone '{drone_id}' already exists.")
        except Exception as e:
            print(f"An error occurred while writing to file '{directory_name}/{drone_id}': {e}")

        self.drones.append(drone)

    #place survivors inside simulation class
    def place_survivors(self, count):
        for _ in range(count):
            x = random.randint(0, GRID_SIZE-1)
            y = random.randint(0, GRID_SIZE-1)
            self.survivors.append((x,y))
            
    
    #drone movement function added
    def move_drone(self, drone_id, x, y): # x and y (and z) simulate real life coordinates for drone movement determined by ai

        for drone in self.drones:
            if drone.id == drone_id:
                drone.move(x,y)
                self.log_state(drone_id)
                return True
            
        return False 
    
    #thermal scan to simulate finding survivors
    def thermal_scan(self, drone_id):

        for drone in self.drones:
            if drone.id == drone_id:

                pos = drone.get_position()
                self.log_state(drone_id)

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

    def log_state(self, drone_id):

        for drone in self.drones:
            if drone.id == drone_id:
                with open(f"{directory_name}/{drone_id}", "a") as f:
                    f.write(f"{drone_id},{temp_current_time},{drone.get_battery()},{drone.get_x_pos()},{drone.get_y_pos()}\n")     