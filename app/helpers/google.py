from typing import List, Tuple
from numba import njit
from polyline import encode as _encode


def encode(coordinates: List[Tuple[float, float]], precision: int = 5, geojson: bool = False) -> str:
    return _encode(coordinates=coordinates, precision=precision, geojson=geojson)


@njit()
def decode(expression: str, geojson: bool = True):
    coords = []
    index = 0
    lat = 0
    lng = 0

    while index < len(expression):
        shift = 0
        result = 0
        while True:
            b = ord(expression[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        shift = 0
        result = 0
        while True:
            b = ord(expression[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        if geojson:
            coords.append((lng * 1e-5, lat * 1e-5))
        else:
            coords.append((lat * 1e-5, lng * 1e-5))

    return coords
