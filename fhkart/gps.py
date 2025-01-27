import logging
import math
import random
import re
import threading
import time
import uuid
from datetime import datetime

import msgspec
import serial


def place(point, other_points, target):
    place = 1
    distance = point.distance(target)
    if other_points == []:
        return place
    for other in other_points:
        if other.distance(target) < distance:
            place += 1

    return place


class GPSBase(msgspec.Struct):
    """GPS data.

    Can be used to calculate distance between two gps points.
    """

    x: float
    y: float

    def distance(self, gps: "GPSBase"):
        """Haversine Formula"""
        r = 6378.137
        d_lat = gps.x * math.pi / 180 - self.x * math.pi / 180
        d_lon = gps.y * math.pi / 180 - self.y * math.pi / 180
        a = math.sin(d_lat / 2) * math.sin(d_lat / 2) + math.cos(
            self.x * math.pi / 180
        ) * math.cos(gps.x * math.pi / 180) * math.sin(d_lon / 2) * math.sin(d_lon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = r * c
        return d * 1000

    @classmethod
    def create(self):
        return GPSBase(random.uniform(54.27, 54.35), random.uniform(10.1, 10.2))

    def as_list(self):
        return [self.x, self.y]


class DBGPS(GPSBase):
    """GPS data from database.

    Has extra id field to identify duplicates.
    Has extra created_at field to sort for last gps
    """

    id: uuid.UUID
    created_at: datetime

    @classmethod
    def create(self):
        return DBGPS(
            random.uniform(54.27, 54.35),
            random.uniform(10.1, 10.2),
            uuid.uuid4(),
            datetime.now(),
        )

    @classmethod
    def from_parser(self, x: float, y: float):
        return DBGPS(
            x,
            y,
            uuid.uuid4(),
            datetime.now(),
        )


class GPSService(threading.Thread):
    def __init__(self, database):
        self.database = database
        self.serial_port = "/dev/ttyUSB3"
        self.baud_rate = 115200
        self.exit = False

        threading.Thread.__init__(self)

    def run(self):
        self.database.post_init()
        self.startup()

        ser = serial.Serial(port=self.serial_port, baudrate=self.baud_rate, timeout=1)
        logging.debug(f"Serial port {self.serial_port} opened successfully.")
        time.sleep(1)
        while not self.exit:
            while True:
                if ser.in_waiting > 0:
                    response = ser.readline().decode().strip()
                    if response != "":
                        (x, y) = self.parse_INF_string(response)
                        gps = DBGPS.from_parser(x, y)
                        logging.debug(f"Inserted new Point {gps}")
                        self.database.insert_gps(gps, self.database.me)
                        self.database.commit()
                    break

            time.sleep(5)

    def startup(self):
        """
        This function Initializes the serial connection
        and configures the GNSS device to output the GPS Data.
        """
        ser = None
        try:
            ser = serial.Serial(
                port=self.serial_port, baudrate=self.baud_rate, timeout=1
            )
            print(f"Serial port {self.serial_port} opened successfully.")
            time.sleep(1)
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
        # else:
        errorCounter = 0
        ser.write("AT\r".encode())
        time.sleep(1)
        while True:
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                if response == "OK":
                    print("SIM7000 Online.")
                    ser.write("AT+CGNSPWR=1\r".encode())
                    time.sleep(1)
                    ser.write("AT+CGNSURC=1\r".encode())
                    time.sleep(1)
                    print("GNSS activated.")
                    break
                elif response == "ERROR" and errorCounter < 5:
                    print("Something went wrong! Trying Again.")
                    ser.write("\r\n".encode())
                    ser.flush()
                    time.sleep(1)
                    ser.write("AT\r".encode())
                    time.sleep(1)
                    ser.flush()
                    errorCounter += 1
                elif errorCounter >= 5:
                    print("Couldnt resolve. Exiting...")
                    break
        # finally:
        #     if "ser" in locals() and ser.is_open:
        #         ser.close()
        #         print("Serial port closed.")

    def parse_INF_string(self, INF_string):
        """
        Extract latitude and longitude from the GNSINF string.

        Its build like this:
        +UGNSINF:
        <GNSS run status>,<Fix status>,<UTC date & Time>,
        <Latitude>,<Longitude>,<MSL Altitude>,<Speed Over
        Ground>,<Course Over Ground>,<Fix
        Mode>,<Reserved1>,<HDOP>,<PDOP>,<VDOP>,<Reserved2>,
        <GNSS Satellites in View>,<GNSS Satellites Used>,
        <GLONASS Satellites Used>,<Reserved3>,<C/N0 max>,
        <HPA>,<VPA>
        """
        match = re.search(
            r"\+UGNSINF: [^,]*,[^,]*,[^,]*,(\d+\.\d+),(\d+\.\d+)", INF_string
        )
        if match:
            latitude = float(match.group(1))
            longitude = float(match.group(2))
            return latitude, longitude
        else:
            raise ValueError(
                f"Coordinates not found in the provided string. Put the Antenna Outdoors, Fool! String {INF_string}"
            )
