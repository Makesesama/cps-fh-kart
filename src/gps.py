import math
import msgspec
import uuid
import random

from datetime import datetime


class GPSBase(msgspec.Struct):
    """GPS data.

    Can be used to calculate distance between two gps points.
    """

    x: float
    y: float

    def distance(self, gps: "GPSBase"):
        return math.dist((self.x, self.y), (gps.x, gps.y))

    @classmethod
    def create(self):
        return GPSBase(random.uniform(54.27, 54.35), random.uniform(10.1, 10.2))


class DBGPS(GPSBase):
    """GPS data from database.

    Has extra id field to identify duplicates.
    Has extra created_at field to sort for last gps
    """

    id: uuid.UUID
    created_at: datetime
