from simulation import Simulation

sim = Simulation()

sim.add_region("Region 1", "R1", "Description of Region 1", [(0,0), (0,10), (10,0), (10,10)])
sim.add_drone("A",0,0, R1)

sim.move_drone("A",4,6)
sim.move_drone("A",2,4)
found = sim.thermal_scan("A")
print("Survivor detected:", found)
