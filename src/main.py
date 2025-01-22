import logging
from argparse import ArgumentParser

from .database import Database
from .helper import get_config_option
from .server import KartClient, KartServer


def main():
    """Main entry point.

    Parses arguments with argparse. Can switch between client and server mode.
    Default is Server.
    """
    logging.basicConfig(level=logging.INFO)

    UDP_IP = get_config_option("TARGET_HOST")
    UDP_PORT = get_config_option("PORT")

    database = get_config_option("DB_PATH")

    parser = ArgumentParser(prog="CPSFHKart")
    parser.add_argument("--mode", default="receive", choices=["receive", "send"])
    args = parser.parse_args()

    if args.mode == "receive":
        KartServer(UDP_IP, UDP_PORT, database)
    elif args.mode == "send":
        KartClient(UDP_IP, UDP_PORT, database)


if __name__ == "__main__":
    main()
