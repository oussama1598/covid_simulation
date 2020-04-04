from manimlib.imports import *
from app.simulations.simple_simulation import SimpleSimulation
from app.modules.graph import Graph


class SimpleSimulationScene(Scene):
    update_frequency = 1 / 15

    def setup(self):
        self.number_of_graphs = 3

        self._add_simulation()
        self._position_camera()
        self._add_graph()

    def construct(self):
        self._run_till_no_infections()

    def _add_simulation(self):
        self.simulation = SimpleSimulation()

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

        frame.next_to(cities.get_right(), LEFT, buff=-0.1 * cities.get_width())

    def _run_till_no_infections(self):
        while True:
            self.wait(20)
            # self.remove(self.simulation)
            # break

            if self.simulation.get_stats()[1] == 0:
                self.wait(5)
                break
