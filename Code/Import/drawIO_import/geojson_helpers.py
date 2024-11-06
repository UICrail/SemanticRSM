import geojson
from fastkml.geometry import LineString
from pyproj import Transformer

# ETRS89-extended / LCC Europe is the default projection
DEFAULT_PROJECTION = "EPSG:3034"
DEFAULT_CENTER_COORDS = 4115023.91, 3536037.64  # of EPSG 3034; somewhere off Norwegian coast

DEFAULT_GEO_REFERENCE = "EPSG:4326"

CANVAS_ORIENTATION = -1

transformer = Transformer.from_crs(DEFAULT_PROJECTION, DEFAULT_GEO_REFERENCE)


def create_geojson_point(x: float | str, y: float | str) -> object:
    """

    :param x:
    :param y:
    :return:
    """
    return geojson.Point(cartesian_to_lonlat((float(x), float(y))))


def cartesian_to_lonlat(*coords: tuple[str | float, str | float]):
    """

    :param coords: array of coordinate pairs (X,Y) [, (X1, Y1)...]
    :return: same but expressed in (longitude, latitude)
    """

    result = []
    for coord in coords:
        result.append(transformer.transform(CANVAS_ORIENTATION * float(coord[1]) + DEFAULT_CENTER_COORDS[1],
                                            float(coord[0]) + DEFAULT_CENTER_COORDS[0]))
    return tuple(result)


def create_geojson_linestring(source: tuple[str | float, str | float], target: tuple[str | float, str | float],
                              *waypoints: tuple[str | float, str | float]) -> LineString:
    """

    :param source: (X,Y) coordinate pair
    :param target: ditto
    :param waypoints: same, between source and target; the sequence source - *waypoints - target must be correct
    :return: GeoJSON Linestring object
    """
    lon_lat_array = ()
    if waypoints:
        lon_lat_array = cartesian_to_lonlat(*waypoints)
    way_coords = (
        cartesian_to_lonlat(source),
        *lon_lat_array,
        cartesian_to_lonlat(target)
    )
    return geojson.LineString(way_coords)
