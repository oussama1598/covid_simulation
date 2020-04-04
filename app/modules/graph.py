import numpy as np
from manimlib.imports import *


class Graph(VGroup):
    def __init__(self, graph_name='Test', simulation=None, color=WHITE, data_index=0, width=5, height=7, update_frequency=1/2, **kwargs):
        super().__init__(**kwargs)

        self.graph_name = graph_name

        self.simulation = simulation
        self.color = color
        self.data_index = data_index

        self.time = 0
        self.last_time_update = -1

        self.update_frequency = update_frequency
        self.width = width
        self.height = height

        self.data = [self.simulation.get_averaged_stats()]

        self._add_axis()
        self._add_data_visualizer()
        self._add_graph_name()

        self.add_updater(lambda obj, dt: self._update_time(dt))
        self.add_updater(lambda obj, dt: self._update_graph(dt))

    def _add_axis(self):
        axes = Axes(
            y_min=0,
            y_max=1,
            y_axis_config={
                "tick_frequency": 0.1,
            },
            x_min=0,
            x_max=1,
            axis_config={
                "include_tip": False,
            },
        )
        origin = axes.c2p(0, 0)
        axes.x_axis.set_width(self.width, about_point=origin, stretch=True)
        axes.y_axis.set_height(self.height, about_point=origin, stretch=True)

        self.add(axes)

        self.axes = axes

    def _add_data_visualizer(self):
        self.data_visualizer = self._visualize_data()

        self.add(self.data_visualizer)

    def _add_graph_name(self):
        position = self.get_corner(DR)

        position[1] = np.array(
            interpolate(self.get_corner(UR)[1], self.get_corner(DR)[1], .5)
        )

        text_obj = TextMobject(self.graph_name, color=self.color)

        text_obj.scale(self.get_height() * .3)
        text_obj.rotate_about_origin(np.pi / 2)
        text_obj.move_to(position + np.array([.3, 0, 0]))

        self.add(text_obj)

    def _visualize_data(self):
        axes = self.axes
        data = self.data

        points = [axes.c2p(0, 0)]

        for x, ys in zip(np.linspace(0, 1, len(data)), data):
            points.append(axes.c2p(x, ys[self.data_index]))

        points.extend([
            axes.c2p(1, 0)
        ])

        region = VMobject()

        region.set_points_as_corners(points)
        region.set_stroke(width=0)
        region.set_fill(self.color, 1)

        return region

    def _update_time(self, delta_time):
        self.time += delta_time

    def _update_graph(self, delta_time):
        if (self.time - self.last_time_update) > self.update_frequency:
            self.data.append(self.simulation.get_averaged_stats())

            self.data_visualizer.become(self._visualize_data())

            self.last_time_update = self.time
