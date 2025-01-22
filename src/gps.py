import math
import msgspec
import uuid
from datetime import datetime


class GPSMock(msgspec.Struct):
    x: float
    y: float

    def distance(self, gps: "GPSMock"):
        return math.dist((self.x, self.y), (gps.x, gps.y))


class DBGPS(GPSMock):
    id: uuid.UUID
    created_at: datetime
