import numpy as np
import random
from manimlib.imports import *
from app.modules.animated import Animated


class Person(Animated):
    time = 0

    def __init__(self, position=np.zeros(3), city_bounds=(None, None), config={}, ** kwargs):
        super().__init__(**kwargs)

        self.colors_set = config['colors_set']

        self.city_bounds = city_bounds

        self.radius = config['radius']
        self.infection_radius = config['infection_radius']

        # Wall buffer is how much likely they'll get near the wall,
        # and the reverse of how much we push them to the middle
        self.wall_buffer = config['wall_buffer']

        # Random movement config
        self.wander_step_size = config['wander_step_size']
        self.wander_step_duration = config['wander_step_duration']
        self.gravity_strength = config['gravity_strength']
        self.last_step_change_time = -1
        self.moving_to = None

        self.p_symptomatic_on_infection = config['p_symptomatic_on_infection']

        # Social Distancing
        self.social_distance_factor = config['social_distance_factor']
        self.repel_from_max_number_of_people = config['repel_from_max_number_of_people']

        self.repel_from_people = []

        self.status = 'S'
        self.max_speed = config['max_speed']
        self.velocity = np.zeros(3)

        self.traveling = False

        # Graphics
        self.dot_obj = None
        self.infection_ring_obj = None

        self._init_position(position)
        self._create_graphics()
        self._listen_for_updates()

    def _init_position(self, position):
        self.position = VectorizedPoint()

        self.add(self.position)
        self.move_to(list(position))

    def _create_graphics(self):
        color = self.colors_set[self.status]

        self.dot_obj = Dot()
        self.infection_ring_obj = Circle(radius=self.infection_radius)

        self.dot_obj.set_height(self.radius)
        self.dot_obj.move_to(self.get_center())
        self.dot_obj.set_color(color)

        self.infection_ring_obj.set_style(
            stroke_color=color,
            stroke_opacity=0,
            stroke_width=1
        )

        self.infection_ring_obj.move_to(self.get_center())

        self.add(self.dot_obj)
        self.add(self.infection_ring_obj)

    def _update_time(self, delta_time):
        self.time += delta_time

    def _move(self, delta_time):
        if self.traveling:
            return

        position = self.get_center()
        force = np.zeros(3)

        if self.wander_step_size != 0:
            if (self.time - self.last_step_change_time) > self.wander_step_duration:
                movement_vector = rotate_vector(RIGHT, TAU * random.random())

                self.moving_to = position + self.wander_step_size * movement_vector
                self.last_step_change = self.time

        if self.moving_to is not None:
            to = (self.moving_to - position)

            dist = get_norm(to)
            if dist != 0:
                force += self.gravity_strength * to / (dist**3)

        wall_force = np.zeros(3)

        infection_radius_array = np.array(
            [self.infection_radius, self.infection_radius, 0]) if self.status == 'I' else np.array([.1, .1, 0])
        lower_bounds_point = self.city_bounds[0] + infection_radius_array
        upper_bounds_point = self.city_bounds[1] - infection_radius_array

        for i in range(2):
            to_upper = upper_bounds_point[i] - position[i]
            to_lower = position[i] - lower_bounds_point[i]

            if to_upper < 0:
                # Make the dot bounce of the wall
                self.velocity[i] = -abs(self.velocity[i])
                # Fix the coordinate so the dot will not go out of the box
                self.set_coord(upper_bounds_point[i], i)

            if to_lower < 0:
                # Make the dot bounce of the wall
                self.velocity[i] = abs(self.velocity[i])
                # Fix the coordinate so the dot will not go out of the box
                self.set_coord(lower_bounds_point[i], i)

            # This force is to ensure that people will not stay apart and it pushed them to the middle
            if to_lower != 0:
                wall_force[i] += max(1 / to_lower - (1 / self.wall_buffer), 0)
            if to_upper != 0:
                wall_force[i] -= max(1 / to_upper - (1 / self.wall_buffer), 0)

        force += wall_force

        if self.social_distance_factor > 0:
            repulsion_force = np.zeros(3)

            min_dist = np.inf

            for point in self.repel_from_people:
                diff_vector = point - self.get_center()
                dist = get_norm(diff_vector)

                if dist > 0:
                    repulsion_force -= self.social_distance_factor * \
                        diff_vector / (dist**3)

            force += repulsion_force

        self.velocity += force * delta_time

        # Constrain the speed
        speed = get_norm(self.velocity)

        if speed > self.max_speed:
            self.velocity *= self.max_speed / speed

        self.shift(self.velocity * delta_time)

    def _listen_for_updates(self):
        self.add_updater(lambda obj, dt: obj._update_time(dt))
        self.add_updater(lambda obj, dt: obj._move(dt))

    def _set_color(self, color):
        self.infection_ring_obj.set_color(color)
        self.dot_obj.set_color(color)

    def set_status(self, status):
        start_color = self.colors_set[self.status]
        end_color = self.colors_set[status]

        self.status = status

        if status == 'I':
            self.infection_start_time = self.time

            if random.random() < self.p_symptomatic_on_infection:
                self.symptomatic = True
            else:
                self.symptomatic = False
                end_color = self.colors_set['A']

            self.add_animation(
                UpdateFromAlphaFunc(
                    self.infection_ring_obj,
                    lambda m, p: m.set_stroke(opacity=interpolate(
                        0, 1, p
                    )),
                    run_time=1,
                )
            )
        else:
            self.add_animation(
                UpdateFromAlphaFunc(
                    self.infection_ring_obj,
                    lambda m, p: m.set_stroke(opacity=interpolate(
                        1, 0, p
                    )),
                    run_time=1,
                )
            )

        self.add_animation(
            UpdateFromAlphaFunc(
                self,
                lambda m, p: m._set_color(interpolate_color(
                    start_color, end_color, p
                )),
                run_time=1,
            )
        )

    def travel_to(self, position, progress):
        self.traveling = True
        self.move_to(position)

        if progress >= 1:
            self.traveling = False
