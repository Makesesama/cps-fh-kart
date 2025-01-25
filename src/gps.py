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
        """Haversine Formula"""
        r = 6378.137
        d_lat = gps.x * math.pi / 180 - self.x * math.pi / 180
        d_lon = gps.y * math.pi / 180 - self.y * math.pi / 180
        a = math.sin(d_lat / 2) * math.sin(d_lat / 2) + math.cos(
            self.x * math.pi / 180
        ) * math.cos(gps.x * math.pi / 180) * math.sin(d_lon / 2) * math.sin(d_lon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = r * c
        return d * 1000

    @classmethod
    def create(self):
        return GPSBase(random.uniform(54.27, 54.35), random.uniform(10.1, 10.2))

    def as_list(self):
        return [self.x, self.y]


class DBGPS(GPSBase):
    """GPS data from database.

    Has extra id field to identify duplicates.
    Has extra created_at field to sort for last gps
    """

    id: uuid.UUID
    created_at: datetime

    @classmethod
    def create(self):
        return DBGPS(
            random.uniform(54.27, 54.35),
            random.uniform(10.1, 10.2),
            uuid.uuid4(),
            datetime.now(),
        )
