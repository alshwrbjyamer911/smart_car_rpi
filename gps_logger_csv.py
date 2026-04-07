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
        print(f"[GPS] Module ready on port {self.port} @ {self.baudrate} baud")

    # -------------------------------------------------
    # Convert NMEA GGA sentence to decimal degrees
    # Returns (lat, lon) if fix, None if no fix, False if not a GGA sentence
    # -------------------------------------------------
    def _parse_gga(self, sentence):

        if not (sentence.startswith("$GNGGA") or sentence.startswith("$GPGGA")):
            return False   # not a GGA sentence at all

        parts = sentence.split(',')

        # parts[6] is fix quality: 0 = no fix
        if len(parts) > 6 and parts[6] == '0':
            print(f"[GPS] GGA received but NO FIX yet (quality=0)")
            return None

        try:
            if len(parts) > 5 and parts[2] and parts[4]:

                lat = float(parts[2])
                lon = float(parts[4])
                lat_dir = parts[3]
                lon_dir = parts[5]

                # Latitude: DDDMM.MMMM → decimal degrees
                lat_deg = int(lat / 100)
                lat_min = lat - (lat_deg * 100)
                lat_decimal = lat_deg + (lat_min / 60)
                if lat_dir == "S":
                    lat_decimal = -lat_decimal

                # Longitude: DDDMM.MMMM → decimal degrees
                lon_deg = int(lon / 100)
                lon_min = lon - (lon_deg * 100)
                lon_decimal = lon_deg + (lon_min / 60)
                if lon_dir == "W":
                    lon_decimal = -lon_decimal

                return lat_decimal, lon_decimal

        except ValueError as e:
            print(f"[GPS] Parse error: {e} on line: {sentence}")
            return None

        return None

    # -------------------------------------------------
    # Log one row to CSV
    # -------------------------------------------------
    def _log_to_csv(self, lat, lon, filename="gps_log.csv", qr_data=None):

        file_exists = os.path.isfile(filename)

        with open(filename, mode="a", newline="") as file:
            writer = csv.writer(file)

            if not file_exists:
                writer.writerow(["timestamp", "latitude", "longitude", "qr_data"])

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([timestamp, lat if lat is not None else "", lon if lon is not None else "", qr_data or ""])

        print(f"[GPS] Logged → lat={lat}, lon={lon}, qr={qr_data}  → {filename}")

    # -------------------------------------------------
    # PUBLIC: Log QR event + best GPS fix available
    # ALWAYS writes a row (even if no GPS fix) so QR detections are never lost
    # -------------------------------------------------
    def get_and_log_once(self, filename="gps_log.csv", max_wait=5, qr_data=None):
        """
        Try to get a GPS fix within max_wait seconds.
        ALWAYS logs a row:
          - With lat/lon if a fix is found
          - With empty lat/lon if no fix (so QR data is never lost)
        Returns (lat, lon) or None.
        """

        lat, lon = None, None

        try:
            gps_serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f"[GPS] Port {self.port} opened OK")
        except Exception as e:
            print(f"[GPS] ERROR opening port {self.port}: {e}")
            # Still log the QR event with no coordinates
            self._log_to_csv(None, None, filename, qr_data=qr_data)
            return None

        start_time = time.time()
        gga_count = 0
        line_count = 0

        while time.time() - start_time < max_wait:

            raw = gps_serial.readline()
            if not raw:
                continue

            line = raw.decode('ascii', errors='replace').strip()
            line_count += 1

            if not line:
                continue

            # Show first 3 unique lines for debugging
            if line_count <= 3:
                print(f"[GPS] Line {line_count}: {line}")

            result = self._parse_gga(line)

            if result is False:
                continue   # not a GGA sentence, skip silently

            gga_count += 1

            if result is None:
                # GGA sentence but no fix yet — keep waiting
                continue

            # Got a valid fix!
            lat, lon = result
            print(f"[GPS] Fix obtained: lat={lat:.6f}, lon={lon:.6f}")
            break

        gps_serial.close()

        if lat is None:
            print(f"[GPS] No fix in {max_wait}s (received {gga_count} GGA sentences, {line_count} total lines) — logging QR only")

        # ALWAYS write the row regardless of fix
        self._log_to_csv(lat, lon, filename, qr_data=qr_data)
        return (lat, lon) if lat is not None else None