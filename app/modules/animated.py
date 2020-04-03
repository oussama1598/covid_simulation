from manimlib.imports import VGroup


class Animated(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.animations = []

        self.add_updater(lambda obj, dt: obj._update_animations())

    def _update_animations(self):
        for animation in self.animations:
            progress = (self.time - animation.start_time) / animation.run_time

            if progress > 1:
                self.remove_animation(animation)
                continue

            animation.interpolate(progress)

    def add_animation(self, animation):
        animation.suspend_mobject_updating = False
        animation.begin()
        animation.start_time = self.time

        self.animations.append(animation)

    def remove_animation(self, animation):
        animation.update(1)
        animation.finish()

        self.animations.remove(animation)
