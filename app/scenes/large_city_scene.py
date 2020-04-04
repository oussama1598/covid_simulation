from app.scenes.simple_simulation_scene import SimpleSimulationScene


class LargeCityScene(SimpleSimulationScene):
    population = 1000

    radius = .2 / 3
    infection_radius = .25
    max_speed = .25
