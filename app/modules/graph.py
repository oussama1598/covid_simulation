from manimlib.imports import VGroup, Axes


class Graph(VGroup):
    def __init__(self, width=5, height=7, **kwargs):
        super().__init__(**kwargs)

        self.time = 0
        self.last_time_update = -1

        self.update_frequency = 1/2
        self.width = width
        self.height = height

        self._add_axis()

        self.add_updater(lambda obj, dt: self._update_time(dt))

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
