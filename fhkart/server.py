import logging
import socket
import threading
import time

import msgspec

from .database import Database
from .gps import DBGPS, GPSBase, GPSService
from .helper import get_ip_address, my_ip, sleep_time
from .payload import Payload


def ping(sock, ip: str, port: int, gps: DBGPS, database):
    """Sends a payload to a socket."""
    payload = Payload(database.me, gps)
    # database.insert_payload(payload)
    packed = msgspec.msgpack.encode(payload)
    sock.sendto(packed, (ip, port))
    logging.debug(f"Send new point {gps} to {ip}:{port}")
    return payload


class GPSMockService(threading.Thread):
    def __init__(self, database):
        self.database = database

        self.exit = False

        threading.Thread.__init__(self)

    def run(self):
        self.database.post_init()
        while not self.exit:
            gps = DBGPS.create()
            logging.debug(f"Inserted new Point {gps}")
            self.database.insert_gps(gps, self.database.me)
            self.database.commit()
            time.sleep(sleep_time)


class PingBackService(threading.Thread):
    def __init__(self, database, port):
        self.database = database
        self.port = port

        self.exit = False

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


class SenderService(threading.Thread):
    def __init__(self, database, ip: str, port: int):
        self.database = database
        self.ip = ip
        self.port = port

        self.exit = False

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


class ReceiverService(threading.Thread):
    def __init__(self, database, ip: str, port: int):
        self.database = database
        self.ip = ip
        self.port = port

        self.exit = False

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
        self.gpsservice = GPSMockService(Database(database))

        if sender_thread:
            self.sending_thread = SenderService(Database(database), ip, port)
            self.sending_thread.start()

        self.gpsservice.start()


class KartServer:
    def __init__(self, ip, port, database, args):
        self.receive_thread = ReceiverService(Database(database), my_ip, port)
        self.receive_thread_alt = ReceiverService(Database(database), "localhost", 8191)
        self.exit = False
        self.ping_back = PingBackService(Database(database), port)

        if args.mock:
            self.gpsservice = GPSMockService(Database(database))
        else:
            self.gpsservice = GPSService(Database(database))

        self.sending_thread = SenderService(Database(database), ip, port)

        self.gpsservice.start()
        self.receive_thread.start()
        self.receive_thread_alt.start()
        self.sending_thread.start()
        self.ping_back.start()
