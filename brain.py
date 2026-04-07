#!/usr/bin/python3
import socket
import json
import time
# -------------------------------
# my driver imports
# -------------------------------
from motor_driver import MotorDriver
from obstacle import process_obstacle
from gps_logger_csv import GPSModule
from qr import QRScanner
import cv2
# -------------------------------
# UDP settings
# -------------------------------
UDP_IP = "0.0.0.0"
LIDAR_PORT = 5005
CAMERA_PORT = 5006
USER_PORT = 5007

# -------------------------------
# Config
# -------------------------------
STOP_THRESHOLD = 25      # cm
RESUME_THRESHOLD = 35    # cm
SIGN_STOP_DIST = 20      # cm
LIDAR_TIMEOUT = 2        # sec
CAMERA_TIMEOUT = 0.5     # sec
USER_TIMEOUT = 1.0       # sec

Kp = 0.5
BASE_SPEED = 1           # just 1=forward, -1=back, 0=stop
STEERING_LEFT = -1
STEERING_RIGHT = 1
STEERING_CENTER = 0
qr_scanner = QRScanner()
gps_module = GPSModule("/dev/ttyAMA0")
# -------------------------------
# Motor setup
# -------------------------------
motor = MotorDriver()
obstacle_blocked = False

# -------------------------------
# Latest sensor data
# -------------------------------
lidar_data = None
camera_data = None
user_data = None
mode = "AUTO"   # default mode

# -------------------------------
# Setup UDP sockets (non-blocking)
# -------------------------------

lidar_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
lidar_sock.bind((UDP_IP, LIDAR_PORT))
lidar_sock.setblocking(False)

camera_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
camera_sock.bind((UDP_IP, CAMERA_PORT))
camera_sock.setblocking(False)

user_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
user_sock.bind((UDP_IP, USER_PORT))
user_sock.setblocking(False)

print("Brain started...")
last_qr = None

# -------------------------------
# Brain loop
# -------------------------------
while True:

    current_time = time.time()

    # -------------------------------
    # 1) Receive UDP packets
    # -------------------------------
    try:
        raw, _ = lidar_sock.recvfrom(4096)
        data = json.loads(raw.decode())
        lidar_data = {
            "distances": data["distances"],
            "timestamp": data["timestamp"]
        }
    except BlockingIOError:
        pass


    try:
        raw, _ = user_sock.recvfrom(4096)
        data = json.loads(raw.decode())
        user_data = {
            "command": data["command"],
            "timestamp": data["timestamp"]
        }
    except BlockingIOError: 
        pass


    # -------------------------------------------------------------
    # !!! CAMERA READ (Preview handled inside read_qr) !!!
    # -------------------------------------------------------------
    qr_data, _ = qr_scanner.read_qr()

    # Check for 'q' key to quit (waitKey is called inside read_qr, but we can check here too)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    if qr_data is not None:
        camera_data = {
            "sign_detected": True,
            "timestamp": current_time
        }
        if qr_data != last_qr:
            print("Detected Sign (New):", qr_data)
            # Log to GPS (module initialized once at top)
            gps_module.get_and_log_once(qr_data=qr_data)
            last_qr = qr_data
            
            motor.stop()
            time.sleep(1.0)


    # -------------------------------
    # auto mode selction based on user command timeout
    # -------------------------------
    if user_data is None:
        mode = "AUTO"
    else:
        # Check if the data is stale rather than getting stuck in MANUAL mode
        if current_time - user_data["timestamp"] > USER_TIMEOUT:
            mode = "AUTO"
        else:
            mode = "MANUAL"

    # -------------------------------
    # 2) MANUAL MODE
    # -------------------------------
    if mode == "MANUAL" and user_data is not None:
        cmd = user_data["command"].lower()
        if cmd == "w":
            motor.forward()
        elif cmd == "s":
            motor.backward()
        elif cmd == "a":
            motor.left()
        elif cmd == "d":
            motor.right()
        else:
            motor.stop()

        time.sleep(0.05)
        continue

    # -------------------------------
    # 3) AUTO MODE
    # -------------------------------
    # --- LIDAR safety ---
    if lidar_data is None or current_time - lidar_data["timestamp"] > LIDAR_TIMEOUT:
        motor.stop()
        time.sleep(0.05)
        continue

    distances = lidar_data["distances"]
    front_indices = [34, 35, 0, 1, 2]
    min_front = min([distances[i] for i in front_indices])
    front_only = front_indices[0]
    if front_only < STOP_THRESHOLD:
        obstacle_blocked = True
    elif front_only > RESUME_THRESHOLD:
        obstacle_blocked = False

    if obstacle_blocked:
        motor.stop()
        time.sleep(0.05)
        override = process_obstacle(distances)
        if override is not None:
            motor.set(override["speed"], override["steering"])
            time.sleep(0.05)
        continue

    time.sleep(0.05)  # 20 Hz loop