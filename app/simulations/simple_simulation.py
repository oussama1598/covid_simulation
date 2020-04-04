from app.modules.simulation import Simulation


class SimpleSimulation(Simulation):
    infection_radius = .75
    gravity_strength = .2
    max_speed = .5
    travel_rate = 0

    pass
