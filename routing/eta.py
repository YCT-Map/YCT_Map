import math


DEFAULT_WALKING_SPEED_METRES_PER_SECOND = 1.35


def eta_seconds(distance_metres, speed=DEFAULT_WALKING_SPEED_METRES_PER_SECOND):
    if distance_metres < 0:
        raise ValueError("Distance cannot be negative.")
    if speed <= 0:
        raise ValueError("Walking speed must be positive.")
    return distance_metres / speed


def format_approximate_eta(seconds):
    if seconds <= 0:
        return "0 min"
    minutes = max(1, math.ceil(seconds / 60))
    return f"~{minutes} min"
