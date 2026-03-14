class Drone:
    def __init__(self, drone_id, x, y):
        self.id = drone_id
        self.x = x
        self.y = y
        self.battery = 100
        self.active = True

    def move(self, new_x, new_y):
        if self.battery <= 0:
            print(f"Drone {self.id} has no battery.")
            return

        self.x = new_x
        self.y = new_y
        self.battery -= 5

    def get_position(self):
        return (self.x, self.y)

    def get_battery(self):
        return self.battery