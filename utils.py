import random


# Generate a list of sleep times from 0.1 to 8.5 in increments of 0.5
MAIN_SLEEP_TIMES = [interval * 0.5 for interval in range(1, 7)]
HIGHER_RANGE_SLEEP_TIME = [interval * 1.0 for interval in range(4, 6)]
MAIN_WEIGHTS = [1 / time for time in MAIN_SLEEP_TIMES]
HIGHER_RANGE_WEIGHTS = [
    0.1 / time for time in HIGHER_RANGE_SLEEP_TIME
]  # Lower weights for higher values
WEIGHTS = MAIN_WEIGHTS + HIGHER_RANGE_WEIGHTS
TOTAL_WEIGHT = sum(WEIGHTS)
# The higher the values the less frequient they'll be
NORMALIZED_WEIGHTS = [weight / TOTAL_WEIGHT for weight in WEIGHTS]


def get_random_weighted_sleep_time():
    global MAIN_SLEEP_TIMES
    global HIGHER_RANGE_SLEEP_TIME
    global NORMALIZED_WEIGHTS
    return random.choices(
        (MAIN_SLEEP_TIMES + HIGHER_RANGE_SLEEP_TIME), weights=NORMALIZED_WEIGHTS, k=1
    )[0]
