import msgspec
import uuid


class Player(msgspec.Struct):
    id: uuid.UUID
    address: str
    me: bool = False
    active: bool = True
