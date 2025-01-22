import math
import msgspec
import uuid
import random

from datetime import datetime


class GPSMock(msgspec.Struct):
    x: float
    y: float

    def distance(self, gps: "GPSMock"):
        return math.dist((self.x, self.y), (gps.x, gps.y))

    @classmethod
    def create(self):
        return GPSMock(random.uniform(1.2, 123141.1), random.uniform(1.2, 123141.1))

    def log(self):
        return f"{self.x} - {self.y}"


class DBGPS(GPSMock):
    id: uuid.UUID
    created_at: datetime
