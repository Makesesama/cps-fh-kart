import threading
import msgspec
import socket
import time
import logging

from .database import Database
from .payload import Payload
from .gps import GPSMock


class KartClient:
    def __init__(self, ip, port, database, sender_thread=True):
        self.exit = False

        self.gps_thread = threading.Thread(
            target=self.get_new_points, args=(Database(database),)
        )

        if sender_thread:
            self.sending_thread = threading.Thread(
                target=self.send, args=(ip, port, Database(database))
            )
            self.sending_thread.start()

        self.gps_thread.start()

    def get_new_points(self, database):
        """GPS thread.

        Gets new GPS data and puts them into the database.
        """
        database.post_init()
        while not self.exit:
            gps = GPSMock.create()
            logging.info(f"Inserted new Point {gps}")
            database.insert_gps(gps, database.me)
            time.sleep(5)

    def ping(self, sock, ip: str, port: int, gps: GPSMock, database):
        """Sends a payload to a socket."""
        payload = Payload(database.me, gps)
        database.insert_payload(payload)
        packed = msgspec.msgpack.encode(payload)
        sock.sendto(packed, (ip, port))
        logging.info(f"Send new point {gps}")
        return payload

    def send(self, ip, port, database):
        """Sending Thread function.

        Sends packets to a server and sleeps for a while
        """
        database.post_init()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        logging.info("Sender started")
        while not self.exit:
            gps = database.select_my_newest()
            self.ping(sock, ip, port, gps, database)

            time.sleep(5)


class KartServer(KartClient):
    def __init__(self, ip, port, database):
        super().__init__(ip, port, database, False)
        self.receive_thread = threading.Thread(
            target=self.receive, args=(ip, port, Database(database))
        )
        self.receive_thread.start()

    def receive(self, ip, port, database):
        """Receiver Thread function.

        Receives the packets of clients. Saves them into Database and registers
        the sender in the database. Also sends saved gps to active players every
        time it receives.
        """

        database.post_init()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((ip, port))
        logging.info("Receiver started")

        while not self.exit:
            # Receive the client packet along with the address it is coming from
            message, address = sock.recvfrom(1024)

            payload = msgspec.msgpack.decode(message, type=Payload)
            payload.player.address = address[0]
            database.insert_payload(payload)
            my_newest_gps = database.select_my_newest()

            # print("My newest", my_newest_gps)
            logging.info(f"Received new point {payload.gps}")
            # print("Their newest", payload.gps)
            # print("Their distance", my_newest_gps.distance(payload.gps))
            # print("Players to ping back", self.database.select_active_players())

            # After every received packet we ping our payload back
            # TODO also ping back other coords so everyone has all data
            for player in database.select_active_players():
                if player.address not in ["localhost", "127.0.0.1"]:
                    self.ping(sock, player.address, port, my_newest_gps, database)
                else:
                    self.ping(sock, player.address, 8002, my_newest_gps, database)
