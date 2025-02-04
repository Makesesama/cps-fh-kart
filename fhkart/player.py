import uuid

import msgspec

from .gps import DBGPS


class Player(msgspec.Struct):
    """Player of the game.

    Saves the address so we can ping him.
    """

    id: uuid.UUID
    address: str
    active: bool = True
    me: bool = False

    def newest_point(self, database):
        return database.select_newest_point(self.id)


class PlayerPoints(Player, kw_only=True):
    points: list[DBGPS]
