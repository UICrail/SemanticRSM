from geopy.distance import geodesic
from shapely import wkt


def linestring_length(ls) -> float:
    """
    Linestring length calculation, assuming WGS84 coordinates.
    Note that this is the length of the 2D projection. geopy does not handle 3D calculations.

    :param ls a WKT linestring
    :return: length of linestring, in meter
    """
    line = wkt.loads(ls)
    return sum(geodesic(line.coords[i], line.coords[i + 1]).m for i in range(len(line.coords) - 1))


if __name__ == '__main__':
    linestring = "LINESTRING (8.2239460999999991 44.0499217999999999, 8.2239935000000006 44.0500031999999990, 8.2241651999999998 44.0502961999999982, 8.2242000999999991 44.0503675000000001, 8.2242733000000001 44.0504865999999993)"
    print(linestring_length(linestring))  # prints the length of LineString in meter
