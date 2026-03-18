import random
import os 
from drone import Drone
from region import Region
import sqlite3

GRID_SIZE = 10

drone_dir_name = "drone_data" 
region_dir_name = "region_data"

temp_current_time = "0400"

# main functions should be that it logs drone state after a certain amount of time and after every action

# TODO: [x] write battery to file
# TODO: adding regions (bc each drone/fleet belongs to a specific region)
# TODO: add system clock
# TODO: make it so it logs state after a couple minutes in system time
# TODO: write time to file
# TODO: connect to agent
# TODO: add exceptions
# TODO: make into csv file instead of txt file for easier parsing and visualization
# TODO: make the lists into dicts
# TODO: RENAME THIS FILE

class Simulation:
    #grid creation for 10x10 disaster map
    def __init__(self):
        self.grid = [["empty" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.drones = {}
        self.regions = {}
        self.survivors = []

    def add_region(self, name, id, description, coordinates):
        region = Region(name, id, description, coordinates)
        try:
            os.mkdir(region_dir_name)
            print(f"Directory '{region_dir_name}' created.")
        except FileExistsError:
            print(f"Directory '{region_dir_name}' already exists.")
        except PermissionError:
            print(f"Permission denied: Unable to create directory '{region_dir_name}'.")
        except Exception as e:
            print(f"An error occurred while creating directory '{region_dir_name}': {e}")
        
        try:
            with open(f"{region_dir_name}/{region.id}", "x") as f:
                f.write(f"drone_id,status,temp_current_time,current_battery,current_x_pos,current_y_pos,\n")
                #self.regions[region.id] = region
        except FileExistsError:
            print(f"Region '{region.id}' already exists.")
        except Exception as e:
            print(f"An error occurred while writing to file '{region_dir_name}/{region.id}': {e}")
        
        self.regions[region.id] = region
    #drones added to simulation class
    def add_drone(self, drone_id, x, y, region_id: str):
        match_region = self.regions.get(region_id)
        if match_region is None:
            print(f"Region '{region_id}' not found. Drone '{drone_id}' not added.")
            return
        drone = Drone(drone_id, x, y, match_region)

        try:
            os.mkdir(drone_dir_name)
            print(f"Directory '{drone_dir_name}' created.")
        except FileExistsError:
            print(f"Directory '{drone_dir_name}' already exists.")
        except PermissionError:
            print(f"Permission denied: Unable to create directory '{drone_dir_name}'.")
        except Exception as e:
            print(f"An error occurred while creating directory '{drone_dir_name}': {e}")
        
        try:
            with open(f"{drone_dir_name}/{drone_id}", "x") as f:
                f.write(f"drone_id,active,temp_current_time,current_battery,current_x_pos,current_y_pos,\n{drone_id},{drone.get_state()},{temp_current_time},{drone.get_battery()},{drone.get_x_pos()},{drone.get_y_pos()}\n")
                # only append drone if file creation is successful, otherwise we will have duplicate entries for the same drone
                self.drones[drone_id] = drone
        except FileExistsError:
            print(f"Drone '{drone_id}' already exists.")
        except Exception as e:
            print(f"An error occurred while writing to file '{drone_dir_name}/{drone_id}': {e}")

        # self.drones.append(drone)

    #place survivors inside simulation class
    def place_survivors(self, count):
        for _ in range(count):
            x = random.randint(0, GRID_SIZE-1)
            y = random.randint(0, GRID_SIZE-1)
            self.survivors.append((x,y))
            
    
    #drone movement function added
    def move_drone(self, drone_id, x, y): # x and y (and z) simulate real life coordinates for drone movement determined by ai

        drone = self.drones.get(drone_id)
        print(self.drones.get(drone_id))
        if drone is None:
            print(f"Drone '{drone_id}' not found. Cannot move.")
            return False
        
        drone.move(x, y)
        self.log_drone_state(drone_id)
        return True
    
    #thermal scan to simulate finding survivors
    def thermal_scan(self, drone_id):

        drone = self.drones.get(drone_id)
        if drone is None:
            print(f"Drone '{drone_id}' not found. Cannot perform thermal scan.")
            return False
        
        pos = drone.get_position()
        self.log_drone_state(drone_id)

        if pos in self.survivors:
            print(f"Survivor found at {pos}")
            return True 
        

    #function to check drone battery
    def get_battery_status(self, drone_id):

        for drone in self.drones:
            if drone.id == drone_id:
                return drone.get_battery()
        return None 

    #return map state (ui)
    def get_map_state(self):

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

    def log_drone_state(self, drone_id):
        for drone in self.drones.values():
            if drone.id == drone_id:
                with open(f"{drone_dir_name}/{drone_id}", "a") as f:
                    f.write(f"{drone_id},{drone.get_state()},{temp_current_time},{drone.get_battery()},{drone.get_x_pos()},{drone.get_y_pos()}\n") 
                with open(f"{region_dir_name}/{drone.region.id}", "a") as f:
                    f.write(f"{drone_id},{drone.get_state()},{temp_current_time},{drone.get_battery()},{drone.get_x_pos()},{drone.get_y_pos()}\n")