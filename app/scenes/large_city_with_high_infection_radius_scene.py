from app.scenes.large_city_scene import LargeCityScene


class LargeCityHighInfectionRadiusScene(LargeCityScene):
    infection_radius = .5

    update_frequency = 1 / 60
