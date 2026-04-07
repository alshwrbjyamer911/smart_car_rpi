# obstacle.py
#!/usr/bin/python3

STOP_THRESHOLD = 25   # cm

STEERING_LEFT  = -1
STEERING_RIGHT =  1

FORWARD_SPEED = 1   # always move forward while steering around obstacle

def process_obstacle(lidar_distances):
    """
    Called only when the car is already blocked (front < STOP_THRESHOLD).

    Input:
        lidar_distances: list of 36 distances in cm (0° to 350°, step 10°)
                         index 0 = 0° (straight ahead), step = 10°
    Output:
        dict with 'speed' and 'steering', or None if front is actually clear
    """
    front_indices = [34, 35, 0, 1, 2]    # -20° to +20°
    left_indices  = [27, 28, 29, 30, 31]  # ~90° left sector
    right_indices = [5,  6,  7,  8,  9]   # ~90° right sector (fixed: was skewed)

    min_front = min(lidar_distances[i] for i in front_indices)
    min_left  = min(lidar_distances[i] for i in left_indices)
    min_right = min(lidar_distances[i] for i in right_indices)

    # Double-check: if front is now safe, let brain handle it
    if min_front > STOP_THRESHOLD:
        return None

    # Pick the side with more free space to steer toward
    if min_left > min_right:
        steering = STEERING_LEFT
        print(f"[obstacle] Turning LEFT  (left_gap={min_left}cm  right_gap={min_right}cm)")
    else:
        steering = STEERING_RIGHT
        print(f"[obstacle] Turning RIGHT (left_gap={min_left}cm  right_gap={min_right}cm)")

    return {
        "speed":    FORWARD_SPEED,
        "steering": steering
    }