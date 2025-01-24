import msgspec
from .gps import GPSBase
from .player import Player


class Payload(msgspec.Struct):
    """Payload to be send to servers."""

    player: Player
    gps: GPSBase
