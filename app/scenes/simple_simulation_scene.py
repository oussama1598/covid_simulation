from manimlib.imports import *
from app.simulations.simple_simulation import SimpleSimulation
from app.modules.graph import Graph


class SimpleSimulationScene(Scene):
    def setup(self):
        self._add_simulation()
        self._position_camera()
        self._add_graph()

    def construct(self):
        self._run_till_no_infections()

    def _add_simulation(self):
        self.simulation = SimpleSimulation()

        self.add(self.simulation)

    def _add_graph(self):
        margin = .3
        frame = self.camera.frame
        frame_height, frame_width = frame.get_height(), frame.get_width()

        simulation_width = self.simulation.get_width()

        graph = Graph(
            # self.simulation,
            width=frame_width - simulation_width - 2,
            height=.75 * frame_height
            # **self.graph_config,
        )

        position = np.array(
            interpolate(frame.get_corner(UL), frame.get_corner(DL), .5)
        )

        position[0] += graph.get_width() / 2 + margin

        graph.move_to(position)

        self.add(graph)

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

            if self.simulation.get_stats()['infected_people'] == 0:
                self.wait(5)
                break
