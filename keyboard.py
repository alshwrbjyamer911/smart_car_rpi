#!/usr/bin/python3

import sys
import tty
import termios
import socket
import json
import time

HOST = "127.0.0.1"
PORT = 5007

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

# Use UDP (must match brain)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("User control started. Press keys (f,b,l,r). q to quit.")

while True:
    key = get_key()

    if key == "q":
        break

    if key.lower() in ["w", "s", "a", "d"]:

        packet = {
            "command": key.lower(),
            "timestamp": time.time()
        }

        sock.sendto(json.dumps(packet).encode(), (HOST, PORT))
        print(f"[SENT] {packet}")

sock.close()
print("User control closed.")