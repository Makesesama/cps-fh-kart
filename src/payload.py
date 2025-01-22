import msgspec
import uuid
from .gps import GPSMock


class Payload(msgspec.Struct):
    player_id: uuid.UUID
    gps: GPSMock
