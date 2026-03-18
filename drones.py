from region import Region

class Drone:
    def __init__(self, drone_id, x, y, Region):
        self.id = drone_id
        self.x = x
        self.y = y
        self.region = Region
        self.battery = 100
        self.active = True
        if self.battery <= 0:
            self.active = False

    def move(self, new_x, new_y):
        if self.battery <= 0:
            print(f"Drone {self.id} has no battery.")
            return

        self.x = new_x
        self.y = new_y
        self.battery -= 5

    def get_position(self):
        return (self.x, self.y)
    
    def get_x_pos(self):
        return self.x
    
    def get_y_pos(self):
        return self.y

    def get_battery(self):
        return self.battery
    
    def get_state(self):
        return self.active
    
    