import random


# Generate a list of sleep times from 0.1 to 8.5 in incerments of 0.5
SLEEP_TIMES = [interval * 0.5 for interval in range(1,18)]
WEIGHTS = [1 / time for time in SLEEP_TIMES]
TOTAL_WEIGHT = sum(WEIGHTS)
# The higher the values the less frequient they'll be
NORMALIZED_WEIGHTS = [weight / TOTAL_WEIGHT for weight in WEIGHTS]
	
	
def get_random_weighted_sleep_time():
	global SLEEP_TIMES
	global NORMALIZED_WEIGHTS
	return random.choices(SLEEP_TIMES, weights=NORMALIZED_WEIGHTS, k=1)[0]
