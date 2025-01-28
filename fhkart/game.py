import uuid
from datetime import datetime

import msgspec

from .gps import GPSBase


class Game(msgspec.Struct):
    """Game."""

    id: int
    target: list[GPSBase]

    def target_as_tuples(self, game_id: int):
        return [
            (str(uuid.uuid4()), gps.x, gps.y, datetime.now(), "game", game_id, True)
            for gps in self.target
        ]
