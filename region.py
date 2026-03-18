class Region:
    # predefined for now
    # TODO: --low priority-- find area between selected coordinates and assign drones to that area
    def __init__(self, name, id, description, coordinates):
        self.name = name
        self.id = id
        self.description = description
        self.coordinates = coordinates
        self.drones = []
    
    def assign_drone(self, drone):
        self.drones.append(drone)
