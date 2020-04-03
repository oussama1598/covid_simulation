class Virus:
    def __init__(self, probability_of_infection_per_day=0.5, infection_duration=5):
        self.probability_of_infection_per_day = probability_of_infection_per_day
        self.infection_duration = infection_duration  # unit days
