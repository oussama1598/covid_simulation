import numpy as np
import random
from manimlib.imports import VGroup, LARGE_BUFF, get_norm, path_along_arc, DEGREES, UpdateFromAlphaFunc, DL, UR, GREEN
from app.modules.city import City
from app.modules.virus import Virus
import copy


class Simulation(VGroup):
    number_of_cities = 1
    city_size = 5
    population = 100

    # Social Distancing
    limit_social_distancing_to_infectious = False

    # Person config
    infection_radius = .2
    wall_buffer = 1 / 3
    wander_step_size = 1
    wander_step_duration = 1
    gravity_strength = 1

    social_distance_factor = 0
    social_distance_color_threshold = 2
    repel_from_max_number_of_people = 10

    max_speed = 1

    p_symptomatic_on_infection = .2

    # Travel
    travel_rate = 0  # .02

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.time = 0
        self.add_updater(lambda obj, dt: obj._update_time(dt))

        self.virus = Virus()

        self.cities = VGroup()

        # For some reason this had to be set up in her otherwise the animation wont work
        self.add_updater(lambda obj, dt: obj._update_statuses(dt))

        self.time_series = []
        self.add_updater(lambda obj: obj._update_stats())

        self._add_cities()
        self._populate_cities()
        # self._infect_random_person()

    def _add_cities(self):
        self.cities = VGroup()

        for x in range(self.number_of_cities):
            self.cities.add(City(
                city_size=self.city_size,
                population=self.population,
                person_config={
                    'infection_radius': self.infection_radius,
                    'wall_buffer': self.wall_buffer,
                    'wander_step_size': self.wander_step_size,
                    'wander_step_duration': self.wander_step_duration,
                    'gravity_strength': self.gravity_strength,
                    'social_distance_factor': self.social_distance_factor,
                    'social_distance_color_threshold': self.social_distance_color_threshold,
                    'repel_from_max_number_of_people': self.repel_from_max_number_of_people,
                    'max_speed': self.max_speed,
                    'p_symptomatic_on_infection': self.p_symptomatic_on_infection
                }
            ))

        self.cities.arrange_in_grid(buff=LARGE_BUFF)

        self.add(self.cities)

    def _populate_cities(self):
        for city in self.cities:
            city.populate()

    def _infect_random_person(self):
        random_city = random.choice(self.cities)
        random_person = random.choice(random_city.people)

        random_person.set_status('I')
        random_person.dot_obj.set_color(GREEN)

    def _update_time(self, delta_time):
        self.time += delta_time

    def _update_statuses(self, delta_time):
        for city in self.cities:
            susceptible_people = list(
                filter(lambda person: person.status == 'S', city.people))
            infected_people = list(
                filter(lambda person: person.status == 'I', city.people))

            for infected_person in infected_people:
                for susceptible_person in susceptible_people:
                    dist_between_the_two = get_norm(
                        infected_person.get_center() - susceptible_person.get_center())

                    if dist_between_the_two < infected_person.infection_radius and random.random() < self.virus.probability_of_infection_per_day:
                        susceptible_person.set_status('I')

                if (infected_person.time - infected_person.infection_start_time) > self.virus.infection_duration:
                    infected_person.set_status('R')

            if self.social_distance_factor > 0 or self.travel_rate > 0:
                for person in susceptible_people + infected_people:
                    if person.social_distance_factor > 0:
                        repel_from_people = infected_people if self.limit_social_distancing_to_infectious else infected_people + susceptible_people
                        repel_from_people_positions = np.array(
                            list(map(lambda x: x.get_center(), repel_from_people)))

                        distances_from_all_repel_people = np.linalg.norm(
                            repel_from_people_positions - person.get_center(), axis=1)

                        person.repel_from_people = repel_from_people_positions[np.argsort(
                            distances_from_all_repel_people)[1:person.repel_from_max_number_of_people + 1]]

                    if self.travel_rate > 0:
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

    def _update_stats(self):
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

        self.time_series.append({
            'time': self.time,
            'susceptible_people': total_susceptible_people,
            'infected_people': total_infected_people,
            'recovered_people': total_recovered_people
        })

    def get_stats(self):
        return self.time_series[-1]
