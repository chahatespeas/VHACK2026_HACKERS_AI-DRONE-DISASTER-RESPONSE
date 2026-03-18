from simulation2 import Simulation

sim = Simulation()
"""

print(sim.regions)

sim.add_drone("A",0,0, "R1")
sim.move_drone("A",4,6)
sim.move_drone("A",2,4)
found = sim.thermal_scan("A")
print("Survivor detected:", found)
"""
sim.add_region("Region 1", "R1", "Description of Region 1", [(0,0), (0,10), (10,0), (10,10)])
sim.add_region("Region 2", "R2", "Description of Region 1", [(5,6), (6,17), (10,2), (1,15)])
sim.add_drone("B",0,0, "R2")
sim.add_drone("C",0,0, "R2")
sim.add_drone("D",0,0, "R1")

sim.move_drone("B",1,1)
sim.move_drone("C",5,5)
sim.move_drone("B",8,1)
sim.move_drone("D",2,4)

