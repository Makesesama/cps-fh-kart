import socket
import random
import msgspec
import time
import uuid
from argparse import ArgumentParser

from .database import Database
from .helper import get_config_option, pack, unpack
from .gps import GPSMock
from .payload import Payload


UDP_IP = get_config_option("TARGET_HOST")
UDP_PORT = get_config_option("PORT")

database = Database(get_config_option("DB_PATH"))


def send(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    while True:
        gps = GPSMock(random.uniform(1.2, 123141.1), random.uniform(1.2, 123141.1))
        payload = Payload(database.me.id, gps)
        packed = msgspec.msgpack.encode(payload)
        print(packed)
        sock.sendto(packed, (ip, port))
        time.sleep(5)


def receive(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))

    while True:
        # Receive the client packet along with the address it is coming from
        message, address = sock.recvfrom(1024)

        payload = msgspec.msgpack.decode(message, type=Payload)
        database.insert_payload(payload)
        print(payload)

        # # Otherwise, the server responds
        # sock.sendto(message, address)


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
