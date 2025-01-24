import msgspec

from .gps import GPSBase


class Game(msgspec.Struct):
    """Game."""

    id: int
    target: GPSBase
