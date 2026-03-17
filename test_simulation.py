from simulation import Simulation

sim = Simulation()

sim.add_drone("A",0,0)
sim.add_drone("B",0,0)
sim.add_drone("C",0,0)

sim.place_survivors(3)

print("Initial State")
print(sim.get_state())

sim.move_drone("A",4,6)
sim.move_drone("B",1,1)
sim.move_drone("C",5,5)

found = sim.thermal_scan("A")

print("Survivor detected:", found)