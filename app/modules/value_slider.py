from manimlib.imports import *


class ValueSlider(NumberLine):
    def __init__(self, name, value, marker_color=BLUE, **kwargs):
        super().__init__(**kwargs)

        self.is_animating = False

        self.marker_color = marker_color

        self.set_width(8, stretch=True)
        self.add_numbers()

        self.marker = ArrowTip(start_angle=-90 * DEGREES)
        self.marker.move_to(self.n2p(value), DOWN)
        self.marker.set_color(self.marker_color)
        self.add(self.marker)

        self.name = TextMobject(name)
        self.name.scale(.9)
        self.name.next_to(self, DOWN)
        self.name.match_color(self.marker)
        self.add(self.name)

    def _update(self, start_value, new_value, progress):
        if 0 < progress < 1:
            self.is_animating = True

        if progress >= 1:
            self.is_animating = False

        interim_value = interpolate(start_value, new_value, progress)
        self.marker.move_to(self.n2p(interim_value), DOWN)

    def get_change_animation(self, new_value):
        self.is_animating = True

        start_value = self.p2n(self.marker.get_bottom())

        return UpdateFromAlphaFunc(
            self,
            lambda obj, p: obj._update(start_value, new_value, p)
        )
