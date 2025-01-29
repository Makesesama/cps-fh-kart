import logging
import math
import random
import threading
import time
import uuid
import gpxpy
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
            random.uniform(54.3307840521, 54.3305306819),
            random.uniform(10.179542899, 10.1799345015),
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


class Track:
    """
    class for handling gpx files and race track progression,
    returns when the player is done
    """

    gps_data: list[GPSBase] = []

    start_pos: GPSBase
    current_pos: GPSBase  # maybe pass this one as arg to the functions?
    target_pos: GPSBase
    current_lap = 1
    lap_goal = 3
    index = 0

    def __init__(self, filepath: str):
        # try:
        with open(filepath, "r") as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            if gpx_file.read() == None:
                raise Exception("File is empty")

            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        self.gps_data.append(GPSBase(point.latitude, point.longitude))

            self.start_pos = self.gps_data[0]
            self.target_pos = self.gps_data[1]

            if (
                self.start_pos is not self.gps_data[-1] and self.lap_goal > 1
            ):  # if last point isnt first point  add it
                self.gps_data.append(
                    self.start_pos
                )  # and more than one lap is required,

            elif (
                self.start_pos is not self.gps_data[-1] and self.lap_goal == 1
            ):  # if last point is not first point and only
                self.start_pos = (self.gps_data[-1],)

                # to ensure check_if_next works
            # except Exception as e:

    def update_current_pos(self, gps):
        self.current_pos = gps

    def check_if_next_one(self):
        """
        checks if the player already reached the next targtet
        and updates it automaticially, counts up lap if necessary
        calls win event if the player is done
        """
        if self.approximate_if_near:
            if self.target_pos == self.start_pos:
                self.current_lap += 1
                self.index = 1
                if self.current_lap > self.lap_goal:
                    self.sendWinImpulse()
            else:
                self.index += 1

            self.target_pos = self.gps_data[self.index]

    def sendWinImpulse():
        pass  # end game, function call / event?

    def approximate_if_near(self):
        quotient_lat = abs(1 - abs(self.current_pos.x / self.target_pos.x))
        quotient_long = abs(1 - abs(self.current_pos.y / self.target_pos.y))
        if (
            quotient_lat < 0.0001 and quotient_long < 0.00000000001
        ):  # less than 0.000000001% inaccuracy, seems fine maybe x10 more
            return True
        else:
            return False


if __name__ == "__main__":
    handler = gpx_handler()
    print(handler.index)
    handler.update_current_pos(GPSBase(50.3370770462, 6.94988250732))
    print(
        "start pos: ",
        handler.start_pos,
        " current pos: ",
        handler.current_pos,
        " target pos: ",
        handler.target_pos,
    )
    if handler.approximate_if_near() == True:
        print("is Near")
    else:
        print("isnt Near")
    handler.check_if_next_one()
    print(handler.index)
