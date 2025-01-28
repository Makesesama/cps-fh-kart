import msgspec
from .gps import GPSBase, DBGPS
from .player import Player


class Payload(msgspec.Struct):
    """Payload to be send to servers."""

    player: Player
    gps: DBGPS

    def __post_init__(self):
        if not self.gps:
            raise ValueError("Gps has to be of type gps")
