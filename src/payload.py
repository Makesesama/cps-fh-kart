import msgspec
from .gps import GPSMock
from .player import Player


class Payload(msgspec.Struct):
    player: Player
    gps: GPSMock
