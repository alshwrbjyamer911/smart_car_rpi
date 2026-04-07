#!/usr/bin/python3
import numpy as np
import serial
import struct
import json
import time
import socket
from enum import Enum

# ----------------------------------------------------------------------
SERIAL_PORT = "/dev/ttyUSB0"
MEASUREMENTS_PER_SCAN = 480
PACKET_LENGTH = 47
MEASUREMENT_LENGTH = 12
MESSAGE_FORMAT = "<xBHH" + "HB" * MEASUREMENT_LENGTH + "HHB"
OUTPUT_FILE = "lidar_scan.json"

# UDP settings
UDP_IP   = "127.0.0.1"
UDP_PORT = 5005

State = Enum("State", ["SYNC0", "SYNC1", "SYNC2", "LOCKED", "PROCESS"])
TARGET_ANGLES = list(range(0, 360, 10))

# ----------------------------------------------------------------------
def parse_packet(data):
    length, speed, start_angle, *pos_data, stop_angle, timestamp, crc = \
        struct.unpack(MESSAGE_FORMAT, data)
    start_angle = float(start_angle) / 100.0
    stop_angle  = float(stop_angle)  / 100.0
    if stop_angle < start_angle:
        stop_angle += 360.0
    step_size = (stop_angle - start_angle) / (MEASUREMENT_LENGTH - 1)
    angles    = [start_angle + step_size * i for i in range(MEASUREMENT_LENGTH)]
    distances = pos_data[0::2]
    confidence= pos_data[1::2]
    return list(zip(angles, distances, confidence))


def build_360_array(measurements):
    measurements.sort(key=lambda m: m[0])
    meas_angles = np.array([m[0] % 360.0 for m in measurements])
    meas_dists  = np.array([m[1] / 1000.0 for m in measurements])
    result = np.zeros(36)
    for i, target in enumerate(TARGET_ANGLES):
        idx = np.argmin(np.abs(meas_angles - target))
        result[i] = round(meas_dists[idx], 3)
    return result


def write_json(arr):
    output = {
        "distances": [int(round(d * 100)) for d in arr.tolist()],
        "timestamp": time.time()
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=4)


def send_udp(sock, distances_cm):
    payload = json.dumps({
        "distances": distances_cm,
        "timestamp": time.time()
    }).encode()
    sock.sendto(payload, (UDP_IP, UDP_PORT))


# ----------------------------------------------------------------------
if __name__ == "__main__":
    lidar_serial = serial.Serial(SERIAL_PORT, 230400, timeout=0.5)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(f"Connected to {SERIAL_PORT}")
    print(f"Sending UDP to {UDP_IP}:{UDP_PORT}\n")

    measurements = []
    data  = b''
    state = State.SYNC0

    while True:
        if state == State.SYNC0:
            data         = b''
            measurements = []
            if lidar_serial.read() == b'\x54':
                data  = b'\x54'
                state = State.SYNC1

        elif state == State.SYNC1:
            byte = lidar_serial.read()
            if byte == b'\x2C':
                data  += b'\x2C'
                state  = State.SYNC2
            else:
                state = State.SYNC0

        elif state == State.SYNC2:
            data += lidar_serial.read(PACKET_LENGTH - 2)
            if len(data) != PACKET_LENGTH:
                state = State.SYNC0
                continue
            measurements += parse_packet(data)
            state = State.LOCKED

        elif state == State.LOCKED:
            data = lidar_serial.read(PACKET_LENGTH)
            if len(data) != PACKET_LENGTH or data[0] != 0x54:
                print("WARNING: Sync lost")
                state = State.SYNC0
                continue
            measurements += parse_packet(data)
            if len(measurements) >= MEASUREMENTS_PER_SCAN:
                state = State.PROCESS

        elif state == State.PROCESS:
            arr = build_360_array(measurements)
            write_json(arr)

            distances_cm = [int(round(d * 100)) for d in arr.tolist()]
            send_udp(sock, distances_cm)

            print(f"[{time.strftime('%H:%M:%S')}] distances(cm): {distances_cm}")

            measurements = []
            state = State.LOCKED