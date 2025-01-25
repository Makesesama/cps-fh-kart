import msgspec
import uuid


class Player(msgspec.Struct):
    """Player of the game.

    Saves the address so we can ping him.
    """

    id: uuid.UUID
    address: str
    me: bool = False
    active: bool = True

    def newest_point(self, database):
        return database.select_newest_point(self.id)
