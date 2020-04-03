import random
import numpy as np
from manimlib.imports import VGroup, WHITE, Square, DL, UR, interpolate
# from app.modules.graphics.Rectangle import Rectangle
from app.modules.person import Person
# from app.helpers.math import interpolate


class City(VGroup):
    def __init__(self, city_size=2, population=100, person_config={}, ** kwargs):
        super().__init__(**kwargs)

        self.time = 0

        self.person_config = person_config

        self.city_size = city_size
        self.population = population

        self.borer_color = WHITE

        self.people = VGroup()

        self._create_graphic()

    def _create_graphic(self):
        rectangle = Square()
        rectangle.set_height(self.city_size)
        rectangle.set_stroke(WHITE, 3)

        self.add(rectangle)

    def populate(self):
        self.position = self.get_center()
        self.bounds = (self.get_corner(DL), self.get_corner(UR))

        for i in range(self.population):
            position = [
                interpolate(lower, upper, random.random())
                for lower, upper in zip(*self.bounds)
            ]

            self.people.add(
                Person(
                    position=position,
                    city_bounds=self.bounds,
                    config=self.person_config
                )
            )

        self.add(self.people)
