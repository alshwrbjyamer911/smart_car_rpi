#!/usr/bin/python3

import serial
import csv
import os
import time
from datetime import datetime


class GPSModule:

    def __init__(self, port="/dev/ttyUSB0", baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    # -------------------------------------------------
    # Convert NMEA to decimal degrees
    # -------------------------------------------------
    def _parse_gga(self, sentence):

        if not (sentence.startswith("$GNGGA") or sentence.startswith("$GPGGA")):
            return None

        parts = sentence.split(',')

        try:
            if len(parts) > 5 and parts[2] and parts[4]:

                lat = float(parts[2])
                lon = float(parts[4])
                lat_dir = parts[3]
                lon_dir = parts[5]

                # Latitude
                lat_deg = int(lat / 100)
                lat_min = lat - (lat_deg * 100)
                lat_decimal = lat_deg + (lat_min / 60)
                if lat_dir == "S":
                    lat_decimal = -lat_decimal

                # Longitude
                lon_deg = int(lon / 100)
                lon_min = lon - (lon_deg * 100)
                lon_decimal = lon_deg + (lon_min / 60)
                if lon_dir == "W":
                    lon_decimal = -lon_decimal

                return lat_decimal, lon_decimal

        except ValueError:
            return None

        return None

    # -------------------------------------------------
    # Log to CSV
    # -------------------------------------------------
    def _log_to_csv(self, lat, lon, filename="gps_log.csv", qr_data=None):

        file_exists = os.path.isfile(filename)

        with open(filename, mode="a", newline="") as file:
            writer = csv.writer(file)

            if not file_exists:
                writer.writerow(["timestamp", "latitude", "longitude", "qr_data"])

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([timestamp, lat, lon, qr_data or ""])

    # -------------------------------------------------
    # PUBLIC FUNCTION
    # -------------------------------------------------
    def get_and_log_once(self, filename="gps_log.csv", max_wait=5, qr_data=None):
        """
        Reads GPS until one valid GGA fix is found.
        Logs it once to CSV (including optional qr_data label).
        Returns (lat, lon) or None if timeout or port unavailable.
        """

        try:
            gps_serial = serial.Serial(
                self.port,
                self.baudrate,
                timeout=self.timeout
            )
        except Exception as e:
            print(f"[GPS] Port open error ({self.port}): {e} – skipping GPS log")
            return None

        start_time = time.time()

        while time.time() - start_time < max_wait:

            line = gps_serial.readline().decode('ascii', errors='replace').strip()

            if not line:
                continue

            result = self._parse_gga(line)

            if result:
                lat, lon = result
                self._log_to_csv(lat, lon, filename, qr_data=qr_data)
                gps_serial.close()
                return lat, lon

        gps_serial.close()
        return None