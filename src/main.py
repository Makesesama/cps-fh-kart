import socket
import random
import msgspec
import time
import uuid
from argparse import ArgumentParser

from .database import Database
from .helper import get_config_option
from .gps import GPSMock
from .payload import Payload


UDP_IP = get_config_option("TARGET_HOST")
UDP_PORT = get_config_option("PORT")

database = Database(get_config_option("DB_PATH"))


def ping(sock, ip: str, port: int, gps: GPSMock):
    payload = Payload(database.me, gps)
    database.insert_payload(payload)
    packed = msgspec.msgpack.encode(payload)
    sock.sendto(packed, (ip, port))
    return payload


def send(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    while True:
        gps = GPSMock(random.uniform(1.2, 123141.1), random.uniform(1.2, 123141.1))
        ping(sock, ip, port, gps)

        time.sleep(5)


def receive(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))

    while True:
        # Receive the client packet along with the address it is coming from
        message, address = sock.recvfrom(1024)

        payload = msgspec.msgpack.decode(message, type=Payload)
        payload.player.address = address[0]
        database.insert_payload(payload)
        my_newest_gps = database.select_my_newest()

        print("My newest", my_newest_gps)
        print("Their newest", payload.gps)
        print("Their distance", my_newest_gps.distance(payload.gps))
        print("Players to ping back", database.select_active_players())

        # After every received packet we ping our payload back
        for player in database.select_active_players():
            if player.address not in ["localhost", "127.0.0.1"]:
                ping(sock, player.address, port, my_newest_gps)


def main():
    parser = ArgumentParser(prog="CPSFHKart")
    parser.add_argument("--mode", default="receive", choices=["receive", "send"])
    args = parser.parse_args()

    if args.mode == "receive":
        receive(UDP_IP, UDP_PORT)
    elif args.mode == "send":
        send(UDP_IP, UDP_PORT)


if __name__ == "__main__":
    main()
