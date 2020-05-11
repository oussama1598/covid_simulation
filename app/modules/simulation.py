import numpy as np
import random
from manimlib.imports import *
from app.modules.city import City
from app.modules.virus import Virus
import copy


class Simulation(VGroup):
    def __init__(self, sliders=False, position=[], height=0, config={}, **kwargs):
        super().__init__(**kwargs)

        self.sliders = sliders
        self.position = position
        self.height = height

        self.number_of_cities = config['number_of_cities']
        self.city_size = config['city_size']
        self.population = config['population']

        # Social Distancing
        self.limit_social_distancing_to_infectious = config['limit_social_distancing_to_infectious']
        self.social_distance_factor = config['social_distance_factor']
        self.repel_from_max_number_of_people = config['repel_from_max_number_of_people']

        # Person config
        self.radius = config['radius']
        self.infection_radius = config['infection_radius']
        self.wall_buffer = config['wall_buffer']
        self.wander_step_size = config['wander_step_size']
        self.wander_step_duration = config['wander_step_duration']
        self.gravity_strength = config['gravity_strength']
        self.p_symptomatic_on_infection = config['p_symptomatic_on_infection']
        self.max_speed = config['max_speed']

        # Virus config
        self.infection_duration = config['infection_duration']
        self.probability_of_infection_per_day = config['probability_of_infection_per_day']

        # Travel config
        self.travel_rate = config['travel_rate']

        self.colors_set = config['colors_set']

        self.time = 0
        self.add_updater(lambda obj, dt: obj._update_time(dt))

        self.virus = Virus(
            infection_duration=self.infection_duration,
            probability_of_infection_per_day=self.probability_of_infection_per_day
        )

        self.cities = VGroup()

        # For some reason this had to be set up in her otherwise the animation wont work
        self.add_updater(lambda obj, dt: obj._update_statuses(dt))

        self._add_cities()
        self._populate_cities()
        self._infect_random_person()

    def _add_cities(self):
        self.cities = VGroup()

        for x in range(self.number_of_cities):
            self.cities.add(City(
                city_size=self.city_size,
                population=self.population,
                person_config={
                    'radius': self.radius,
                    'colors_set': self.colors_set,
                    'infection_radius': self.infection_radius,
                    'wall_buffer': self.wall_buffer,
                    'wander_step_size': self.wander_step_size,
                    'wander_step_duration': self.wander_step_duration,
                    'gravity_strength': self.gravity_strength,
                    'social_distance_factor': self.social_distance_factor,
                    'repel_from_max_number_of_people': self.repel_from_max_number_of_people,
                    'max_speed': self.max_speed,
                    'p_symptomatic_on_infection': self.p_symptomatic_on_infection
                }
            ))

        self.cities.arrange_in_grid(buff=LARGE_BUFF)
        self.cities.set_height(self.height)

        width, height = self.cities.get_width(), self.cities.get_height()
        margin = np.array(
            [(-width / 2) - (.2 if self.sliders else 0), (-height / 2) if self.sliders else 0, 0])

        self.cities.move_to(
            self.position + margin)

        self.add(self.cities)

    def _populate_cities(self):
        for city in self.cities:
            city.populate()

    def _infect_random_person(self):
        random_city = random.choice(self.cities)
        random_person = random.choice(random_city.people)

        random_person.set_status('I')

    def _update_time(self, delta_time):
        self.time += delta_time

    def _update_statuses(self, delta_time):
        for slider in self.sliders:
            if slider.is_animating:
                return

        for city in self.cities:
            susceptible_people = list(
                filter(lambda person: person.status == 'S', city.people))
            infected_people = list(
                filter(lambda person: person.status == 'I', city.people))
            recovered_people = list(
                filter(lambda person: person.status == 'I', city.people))

            for infected_person in infected_people:
                for susceptible_person in susceptible_people:
                    dist_between_the_two = get_norm(
                        infected_person.get_center() - susceptible_person.get_center())

                    if dist_between_the_two < infected_person.infection_radius and random.random() < self.virus.probability_of_infection_per_day:
                        susceptible_person.set_status('I')

                if (infected_person.time - infected_person.infection_start_time) > self.virus.infection_duration:
                    infected_person.set_status('R')

                for person in susceptible_people + infected_people:
                    person.repel_from_people = []

                    if person.social_distance_factor > 0:
                        repel_from_people = infected_people if self.limit_social_distancing_to_infectious else infected_people + susceptible_people
                        repel_from_people_positions = np.array(
                            list(map(lambda x: x.get_center(), repel_from_people)))

                        distances_from_all_repel_people = np.linalg.norm(
                            repel_from_people_positions - person.get_center(), axis=1)

                        person.repel_from_people = repel_from_people_positions[np.argsort(
                            distances_from_all_repel_people)[1:person.repel_from_max_number_of_people + 1]]

                    if self.travel_rate > 0 and len(self.cities) > 1:
                        path_func = path_along_arc(45 * DEGREES)

                        if random.random() < self.travel_rate * delta_time:
                            travel_to_city = random.choice(
                                [city_to for city_to in self.cities if city_to != city])

                            # remove person for the old city
                            city.people.remove(person)

                            # add the person to the next city
                            travel_to_city.people.add(person)

                            person.city_bounds = travel_to_city.bounds

                            old_center = person.get_center()

                            person.add_animation(
                                UpdateFromAlphaFunc(
                                    person,
                                    lambda m, p: m.travel_to(path_func(
                                        old_center, travel_to_city.position, p,
                                    ), p),
                                    run_time=1,
                                )
                            )

                for person in recovered_people:
                    person.repel_from_people = []

    def get_stats(self):
        total_susceptible_people = 0
        total_infected_people = 0
        total_recovered_people = 0

        for city in self.cities:
            total_susceptible_people += len(list(
                filter(lambda person: person.status == 'S', city.people)))
            total_infected_people += len(list(
                filter(lambda person: person.status == 'I', city.people)))
            total_recovered_people += len(list(
                filter(lambda person: person.status == 'R', city.people)))

        return np.array([
            total_susceptible_people,
            total_infected_people,
            total_recovered_people
        ])

    def get_averaged_stats(self):
        stats = self.get_stats()

        return stats / sum(stats)

    def change_social_distance_factor(self, new_value, social_distancing_probability):
        self.social_distance_factor = new_value

        for city in self.cities:
            for person in city.people:
                if random.random() < social_distancing_probability:
                    person.social_distance_factor = new_value
