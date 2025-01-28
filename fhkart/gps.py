import logging
import math
import random
import threading
import time
import uuid
from datetime import datetime

import msgspec


def place(point, other_points, target):
    place = 1
    distance = point.distance(target)
    if other_points == []:
        return place
    for other in other_points:
        if other.distance(target) < distance and point.id != other.id:
            place += 1

    return place


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
            random.uniform(54.330723, 54.329224),
            random.uniform(10.189832, 10.182837),
            uuid.uuid4(),
            datetime.now(),
        )

    @classmethod
    def from_parser(self, x: float, y: float):
        return DBGPS(
            x,
            y,
            uuid.uuid4(),
            datetime.now(),
        )
