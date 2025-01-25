import threading
import msgspec
import socket
import time
import logging

from .database import Database
from .payload import Payload
from .gps import GPSBase, DBGPS


def ping(sock, ip: str, port: int, gps: DBGPS, database):
    """Sends a payload to a socket."""
    payload = Payload(database.me, gps)
    # database.insert_payload(payload)
    packed = msgspec.msgpack.encode(payload)
    sock.sendto(packed, (ip, port))
    logging.info(f"Send new point {gps} to {ip}:{port}")
    return payload


class GPSService(threading.Thread):
    def __init__(self, database):
        self.database = database

        self.exit = False

        threading.Thread.__init__(self)

    def run(self):
        self.database.post_init()
        while not self.exit:
            gps = DBGPS.create()
            logging.info(f"Inserted new Point {gps}")
            self.database.insert_gps(gps, self.database.me)
            self.database.commit()
            time.sleep(5)


class PingBackService(threading.Thread):
    def __init__(self, database, alternative_port: int):
        self.database = database
        self.alternative_port = alternative_port

        self.exit = False

        threading.Thread.__init__(self)

    def run(self):
        self.database.post_init()
        while not self.exit:
            gps = self.database.select_my_newest_point()
            players = self.database.select_active_players()
            print("players", players)

            self.send_players(players, 8000, gps, self.database)
            time.sleep(5)

    def send_players(self, players, port, gps, database):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

        for player in players:
            if not player.me:
                print(player)
                if player.address not in ["localhost", "127.0.0.1"]:
                    logging.info(f"Sending to player {str(player.id)}")
                    ping(sock, player.address, 8000, gps, database)
                else:
                    ping(sock, player.address, self.alternative_port, gps, database)
            time.sleep(5)


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
        logging.info("Sender started")
        while not self.exit:
            gps = self.database.select_my_newest_point()
            ping(sock, self.ip, self.port, gps, self.database)

            time.sleep(5)


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
        logging.info("Receiver started")

        while not self.exit:
            # Receive the client packet along with the address it is coming from
            message, address = sock.recvfrom(1024)

            payload = msgspec.msgpack.decode(message, type=Payload)
            payload.player.address = address[0]
            self.database.insert_payload(payload)

            logging.info(f"Received new point {payload.gps}")


class KartClient:
    def __init__(self, ip, port, database, sender_thread=False):
        self.exit = False
        self.gpsservice = GPSService(Database(database))

        if sender_thread:
            self.sending_thread = SenderService(Database(database), "localhost", 8000)
            self.sending_thread.start()

        self.gpsservice.start()


class KartServer:
    def __init__(self, ip, port, database):
        self.receive_thread = ReceiverService(Database(database), "localhost", 8000)
        self.receive_thread_alt = ReceiverService(Database(database), "localhost", 8191)
        self.exit = False
        self.ping_back = PingBackService(Database(database), 8191)
        self.gpsservice = GPSService(Database(database))

        self.sending_thread = SenderService(Database(database), "localhost", 8000)

        self.gpsservice.start()
        self.receive_thread.start()
        self.receive_thread_alt.start()
        self.sending_thread.start()
        self.ping_back.start()
