import math
import msgspec
import uuid
import random

from datetime import datetime


class GPSMock(msgspec.Struct):
    """GPS data.

    Can be used to calculate distance between two gps points.
    """

    x: float
    y: float

    def distance(self, gps: "GPSMock"):
        return math.dist((self.x, self.y), (gps.x, gps.y))

    @classmethod
    def create(self):
        return GPSMock(random.uniform(1.2, 123141.1), random.uniform(1.2, 123141.1))


class DBGPS(GPSMock):
    """GPS data from database.

    Has extra id field to identify duplicates.
    Has extra created_at field to sort for last gps
    """

    id: uuid.UUID
    created_at: datetime
