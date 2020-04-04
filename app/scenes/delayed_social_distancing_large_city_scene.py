from app.scenes.large_city_scene import LargeCityScene
from app.scenes.delayed_social_distancing_scene import DelayedSocialDistancingScene


class DelayedSocialDistancingLargeCityScene(DelayedSocialDistancingScene, LargeCityScene):
    infection_threshold = 50
    population = 900

    def construct(self):
        self.wait_until_infection_threshold(self.infection_threshold)

        self.simulation.change_social_distance_factor(
            self.target_social_distancing_factor,
            self.social_distancing_probability
        )

        self.play(
            self.sliders[0].get_change_animation(
                self.target_social_distancing_factor
            )
        )

        self._run_till_no_infections()
