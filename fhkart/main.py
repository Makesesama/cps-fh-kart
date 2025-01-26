import logging
from argparse import ArgumentParser

from .helper import get_config_option, get_logging_option
from .server import KartClient, KartServer
from .gui import start_gui


def main():
    """Main entry point.

    Parses arguments with argparse. Can switch between client and server mode.
    Default is Server.
    """
    logging.basicConfig(level=get_logging_option())

    UDP_IP = get_config_option("TARGET_HOST")
    UDP_PORT = get_config_option("PORT")

    database = get_config_option("DB_PATH")

    parser = ArgumentParser(prog="CPSFHKart")

    parser.add_argument("--mode", default="gui", choices=["receive", "send", "gui"])

    parser.add_argument(
        "target",
        help="The target ip or hostname the program should try to ping",
        type=str,
    )

    args = parser.parse_args()

    if args.mode == "receive":
        KartServer(UDP_IP, UDP_PORT, database)
    elif args.mode == "send":
        KartClient(UDP_IP, UDP_PORT, database)
    elif args.mode == "gui":
        start_gui(database, args.target, UDP_PORT)


def start():
    main()


if __name__ == "__main__":
    main()
