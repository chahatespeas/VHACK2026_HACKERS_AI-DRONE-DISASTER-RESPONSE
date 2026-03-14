from simulation import Simulation

sim = Simulation()

sim.add_drone("A",0,0)
sim.add_drone("B",2,2)
sim.add_drone("C",5,5)

sim.place_survivors(3)

print("Initial State")
print(sim.get_state())

sim.move_drone("A",4,6)

found = sim.thermal_scan("A")

print("Survivor detected:", found)