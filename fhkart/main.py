import logging
from argparse import ArgumentParser

from .database import Database, DBInfo
from .game import Game
from .gps import GPSBase
from .gui import start_gui
from .helper import get_config_option, get_logging_option
from .server import KartClient, KartServer


def main():
    """Main entry point.

    Parses arguments with argparse. Can switch between client and server mode.
    Default is Server.
    """
    logging.basicConfig(level=get_logging_option())

    UDP_IP = get_config_option("TARGET_HOST")
    UDP_PORT = get_config_option("PORT")

    db_path = get_config_option("DB_PATH")

    parser = ArgumentParser(prog="CPSFHKart")

    parser.add_argument("--mode", default="gui", choices=["receive", "send", "gui"])

    parser.add_argument(
        "target",
        help="The target ip or hostname the program should try to ping",
        type=str,
    )
    parser.add_argument("--mock", default=False, help="For testing set mock to true")
    parser.add_argument(
        "--target-gps-x", default=54.332262, help="The target", type=float
    )
    parser.add_argument(
        "--target-gps-y", default=10.180552, help="The target", type=float
    )

    args = parser.parse_args()

    game = Database.for_pre_init(db_path)
    database = DBInfo(
        path=db_path,
        game=Game(game.id + 1, target=GPSBase(args.target_gps_x, args.target_gps_y)),
    )
    if args.mode == "receive":
        KartServer(UDP_IP, UDP_PORT, database, args)
    elif args.mode == "send":
        KartClient(UDP_IP, UDP_PORT, database, args)
    elif args.mode == "gui":
        start_gui(database, args.target, UDP_PORT, args)


def start():
    main()


if __name__ == "__main__":
    main()
