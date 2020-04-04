from manimlib.imports import *
from app.modules.value_slider import ValueSlider
from app.scenes.simple_simulation_scene import SimpleSimulationScene


class DelayedSocialDistancingScene(SimpleSimulationScene):
    delay_duration = 8
    target_social_distancing_factor = 2
    social_distancing_probability = 1

    def construct(self):
        self.wait(self.delay_duration)

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

    def _add_sliders(self):
        self.sliders = VGroup()

        self.sliders.add(ValueSlider(
            'Social Distancing Factor',
            value=0,
            x_min=0,
            x_max=2,
            tick_frequency=0.5,
            numbers_with_elongated_ticks=[],
            numbers_to_show=range(3),
            decimal_number_config={
                "num_decimal_places": 0,
            }
        ))

        self.add(self.sliders)
