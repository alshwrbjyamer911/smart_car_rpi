# obstacle.py
#!/usr/bin/python3
import math

STOP_THRESHOLD = 25   # cm
RESUME_THRESHOLD = 35 # cm

STEERING_LEFT = -1
STEERING_RIGHT = 1
STEERING_CENTER = 0

BASE_SPEED = 1
TURN_SPEED = 1

def process_obstacle(lidar_distances):
    """
    Input:
        lidar_distances: list of 36 distances in cm (0° to 350°, step 10°)
    Output:
        override: dict with 'speed' and 'steering'
                  or None if no override needed
    """
    front_indices = [34, 35, 0, 1, 2]   # -20° to +20°
    left_indices  = [27, 28, 29, 30, 31] # left sector
    right_indices = [7, 8, 9, 10, 11]   # right sector

    min_front = min([lidar_distances[i] for i in front_indices])
    min_left  = min([lidar_distances[i] for i in left_indices])
    min_right = min([lidar_distances[i] for i in right_indices])

    # If front is safe, no override
    if min_front > STOP_THRESHOLD:
        return None

    # Reactive avoidance
    # Choose the side with more space
    if min_left > min_right:
        steering = STEERING_LEFT
    else:
        steering = STEERING_RIGHT

    # Slow forward movement while turning
    speed = TURN_SPEED if min_front < STOP_THRESHOLD else BASE_SPEED

    return {
        "speed": speed,
        "steering": steering
    }