import msgspec
from .gps import GPSMock
from .player import Player


class Payload(msgspec.Struct):
    """Payload to be send to servers."""

    player: Player
    gps: GPSMock
