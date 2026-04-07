#!/usr/bin/python3
import serial
import time

gps_serial = serial.Serial(
    "/dev/ttyUSB1",  # UART
    baudrate=9600,
    timeout=1
)

def parse_nmea(sentence):
    """
    Safe NMEA parser for GGA sentences
    """
    if sentence.startswith("$GNGGA") or sentence.startswith("$GPGGA"):
        parts = sentence.split(',')
        try:
            if len(parts) > 5 and parts[2] and parts[4]:
                # Make sure latitude and longitude are valid floats
                lat = float(parts[2])
                lon = float(parts[4])
                lat_dir = parts[3]
                lon_dir = parts[5]

                # Convert to decimal degrees
                lat_deg = int(lat / 100)
                lat_min = lat - (lat_deg * 100)
                lat_decimal = lat_deg + (lat_min / 60)
                if lat_dir == "S":
                    lat_decimal = -lat_decimal

                lon_deg = int(lon / 100)
                lon_min = lon - (lon_deg * 100)
                lon_decimal = lon_deg + (lon_min / 60)
                if lon_dir == "W":
                    lon_decimal = -lon_decimal

                print(f"Latitude: {lat_decimal:.6f}, Longitude: {lon_decimal:.6f}")
                print(f"Latitude: {lat_decimal:.6f}, Longitude: {lon_decimal:.6f}")
                print(f"Google Maps: https://www.google.com/maps?q={lat_decimal},{lon_decimal}")
            

        except ValueError:
            #print('fuckk')
            # Skip lines with non-numeric fields
            pass

try:
    while True:
        line = gps_serial.readline().decode('ascii', errors='replace').strip()
        #print(line)
        if line:
            parse_nmea(line)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    gps_serial.close()
