import msgspec


class GPSMock(msgspec.Struct):
    x: float
    y: float
