import msgspec
import uuid


class Player(msgspec.Struct):
    id: uuid.UUID
    me: bool
    active: bool = True
