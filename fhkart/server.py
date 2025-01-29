import logging
import socket
import threading
import time
import re
import serial
import msgspec

from .database import Database, DBInfo, DBWrapper
from .gps import DBGPS, GPSBase
from .helper import get_ip_address, my_ip, sleep_time
from .payload import Payload


def ping(sock, ip: str, port: int, gps: DBGPS, database):
    """Sends a payload to a socket."""
    try:
        payload = Payload(database.me, gps)
        # database.insert_payload(payload)
        packed = msgspec.msgpack.encode(payload)
        sock.sendto(packed, (ip, port))
        logging.debug(f"Send new point {gps} to {ip}:{port}")
        return payload
    except ValueError:
        pass


class GPSMockService(threading.Thread, DBWrapper):
    def __init__(self, database):
        DBWrapper.__init__(self, database)

        threading.Thread.__init__(self)

    def run(self):
        self.database.post_init()
        while not self.exit:
            gps = DBGPS.create()
            logging.debug(f"Inserted new Point {gps}")
            self.database.insert_gps(gps, self.database.me)
            self.database.commit()
            time.sleep(sleep_time)


class GPSService(threading.Thread, DBWrapper):
    def __init__(self, database):
        DBWrapper.__init__(self, database)
        self.serial_port = "/dev/ttyUSB3"
        self.baud_rate = 115200

        threading.Thread.__init__(self)

    def run(self):
        self.database.post_init()
        self.startup()

        ser = serial.Serial(port=self.serial_port, baudrate=self.baud_rate, timeout=1)
        logging.debug(f"Serial port {self.serial_port} opened successfully.")
        time.sleep(1)
        while not self.exit:
            try:
                while True:
                    bytesToRead = ser.inWaiting()
                    response = ser.read(bytesToRead).decode().strip()
                    if len(response) > 0:
                        (x, y) = self.parse_INF_string(response)
                        gps = DBGPS.from_parser(x, y)
                        logging.debug(f"Inserted new Point {gps}")
                        self.database.insert_gps(gps, self.database.me)
                        self.database.commit()

            except:
                continue

            time.sleep(5)

    def startup(self):
        """Initializes serial connection with gps module."""
        ser = None
        try:
            ser = serial.Serial(
                port=self.serial_port, baudrate=self.baud_rate, timeout=1
            )
            print(f"Serial port {self.serial_port} opened successfully.")
            time.sleep(1)
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")

        errorCounter = 0
        ser.write("AT\r".encode())
        time.sleep(1)
        while True:
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                if response == "OK":
                    logging.info("SIM7000 Online.")
                    ser.write("AT+CGNSPWR=1\r".encode())
                    time.sleep(1)
                    ser.write("AT+CGNSURC=1\r".encode())
                    time.sleep(1)
                    logging.info("GNSS activated.")
                    break
                elif response == "ERROR" and errorCounter < 5:
                    logging.error("Something went wrong! Trying Again.")
                    ser.write("\r\n".encode())
                    ser.flush()
                    time.sleep(1)
                    ser.write("AT\r".encode())
                    time.sleep(1)
                    ser.flush()
                    errorCounter += 1
                elif errorCounter >= 5:
                    logging.error("Couldnt resolve. Exiting...")
                    break

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


class PingBackService(threading.Thread, DBWrapper):
    def __init__(self, database, port):
        DBWrapper.__init__(self, database)
        self.port = port

        threading.Thread.__init__(self)

    def run(self):
        self.database.post_init()
        while not self.exit:
            gps = self.database.select_my_newest_point()
            players = self.database.select_active_players()

            self.send_players(players, self.port, gps, self.database)
            time.sleep(sleep_time)

    def send_players(self, players, port, gps, database):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

        for player in players:
            if not player.me:
                if player.address not in ["localhost", "127.0.0.1", my_ip]:
                    logging.debug(f"Sending to player {str(player.id)}")
                    ping(sock, player.address, port, gps, database)
                else:
                    ping(sock, player.address, port, gps, database)
            time.sleep(sleep_time)


class SenderService(threading.Thread, DBWrapper):
    def __init__(self, database, ip: str, port: int):
        DBWrapper.__init__(self, database)
        self.ip = ip
        self.port = port

        threading.Thread.__init__(self)

    def run(self):
        """Sending Thread function.

        Sends packets to a server and sleeps for a while
        """
        self.database.post_init()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        logging.debug("Sender started")
        while not self.exit:
            gps = self.database.select_my_newest_point()
            ping(sock, self.ip, self.port, gps, self.database)

            time.sleep(sleep_time)


class ReceiverService(threading.Thread, DBWrapper):
    def __init__(self, database, ip: str, port: int):
        DBWrapper.__init__(self, database)
        self.ip = ip
        self.port = port

        threading.Thread.__init__(self)

    def run(self):
        self.database.post_init()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.ip, self.port))
        logging.debug("Receiver started")

        while not self.exit:
            # Receive the client packet along with the address it is coming from
            message, address = sock.recvfrom(1024)

            payload = msgspec.msgpack.decode(message, type=Payload)
            payload.player.address = address[0]
            self.database.insert_payload(payload)

            logging.debug(f"Received new point {payload.gps}")


class KartClient:
    def __init__(self, ip, port, database, sender_thread=False):
        self.exit = False
        self.gpsservice = GPSMockService(database)

        if sender_thread:
            self.sending_thread = SenderService(database, ip, port)
            self.sending_thread.start()

        self.gpsservice.start()


class KartServer:
    def __init__(self, ip, port, database, args):
        self.receive_thread = ReceiverService(database, my_ip, port)
        self.receive_thread_alt = ReceiverService(database, "localhost", 8191)
        self.exit = False
        self.ping_back = PingBackService(database, port)

        if args.mock:
            self.gpsservice = GPSMockService(database)
        else:
            self.gpsservice = GPSService(database)

        self.sending_thread = SenderService(database, ip, port)

        self.gpsservice.start()
        self.receive_thread.start()
        self.receive_thread_alt.start()
        self.sending_thread.start()
        self.ping_back.start()
