from manimlib.imports import *
from app.modules.simulation import Simulation
from app.modules.graph import Graph


class SimpleSimulationScene(Scene):
    number_of_cities = 1
    city_size = 7
    population = 100

    # Social Distancing
    limit_social_distancing_to_infectious = False

    # Person config
    radius = .1
    infection_radius = .6
    wall_buffer = 1 / 3
    wander_step_size = 1
    wander_step_duration = 1
    gravity_strength = .2

    social_distance_factor = 0
    repel_from_max_number_of_people = 10

    max_speed = .5

    p_symptomatic_on_infection = 1

    # Virus config
    infection_duration = 5
    probability_of_infection_per_day = .2

    # Travel
    travel_rate = 0

    colors_set = {
        'S': BLUE,
        'I': RED,
        'R': WHITE,
        'A': YELLOW
    }

    update_frequency = 1 / 15

    def setup(self):
        self.sliders = None

        self.number_of_graphs = 3

        self._add_sliders()
        self._add_simulation()
        self._position_camera()
        self._add_graph()
        self._position_sliders()

    def construct(self):
        self._run_till_no_infections()

    def _add_simulation(self):
        height = self.camera.frame.get_height() * .9
        position = np.array([self.camera.frame.get_corner(
            UR)[0], self.camera.frame.get_center()[1], 0])

        if self.sliders:
            height = self.camera.frame.get_height() - self.sliders.get_height()
            position = self.camera.frame.get_corner(UR)

        self.simulation = Simulation(
            sliders=self.sliders != None,
            position=position,
            height=height,
            config={
                'number_of_cities': self.number_of_cities,
                'city_size': self.city_size,
                'population': self.population,
                'limit_social_distancing_to_infectious': self.limit_social_distancing_to_infectious,
                'radius': self.radius,
                'infection_radius': self.infection_radius,
                'wall_buffer': self.wall_buffer,
                'wander_step_size': self.wander_step_size,
                'wander_step_duration': self.wander_step_duration,
                'gravity_strength': self.gravity_strength,
                'social_distance_factor': self.social_distance_factor,
                'repel_from_max_number_of_people': self.repel_from_max_number_of_people,
                'max_speed': self.max_speed,
                'p_symptomatic_on_infection': self.p_symptomatic_on_infection,
                'infection_duration': self.infection_duration,
                'probability_of_infection_per_day': self.probability_of_infection_per_day,
                'travel_rate': self.travel_rate,
                'colors_set': self.colors_set
            }
        )

        self.add(self.simulation)

    def _add_graph(self):
        graphs = VGroup()

        margin = .3
        frame = self.camera.frame
        frame_height, frame_width = frame.get_height(), frame.get_width()

        simulation_width = self.simulation.get_width()

        for data_index, graph_name, color_name in zip(range(3), ['Susceptible', 'Infected', 'Recovered'], 'SIR'):
            graphs.add(Graph(
                graph_name=graph_name,
                simulation=self.simulation,
                width=frame_width - simulation_width - 2,
                height=(frame_height / self.number_of_graphs) -
                (self.number_of_graphs * .3),
                color=self.simulation.colors_set[color_name],
                data_index=data_index,
                update_frequency=self.update_frequency
                # **self.graph_config,
            ))

        position = np.array(
            interpolate(frame.get_corner(UL), frame.get_corner(DL), .5)
        )

        position[0] += graphs.get_width() / 2 + margin

        graphs.arrange_in_grid(buff=MED_LARGE_BUFF)
        graphs.move_to(position)

        self.add(graphs)

    def _add_sliders(self):
        pass

    def _position_sliders(self):
        if self.sliders:
            width, height = self.simulation.get_width() - 2, self.sliders.get_height()
            position = self.camera.frame.get_corner(DR)

            position[0] = self.simulation.get_center()[0]

            self.sliders.set_width(width)
            self.sliders.move_to(position + np.array([0, height / 2, 0]))

    def _position_camera(self):
        frame = self.camera.frame
        cities = self.simulation.cities

        cities_height = cities.get_height() + 1
        cities_width = cities.get_width()

        # set the frame height to be as the cities box height
        if cities_height > frame.get_height():
            frame.set_height(cities_height)

        # set the frame width to be as the cities box width
        if cities_width > frame.get_width():
            frame.set_width(cities_width)

    def _run_till_no_infections(self):
        while True:
            self.wait(5)

            if self.simulation.get_stats()[1] == 0:
                self.wait(5)
                break

    def wait_until_infection_threshold(self, threshold):
        self.wait_until(
            lambda: self.simulation.get_stats()[1] > threshold
        )
