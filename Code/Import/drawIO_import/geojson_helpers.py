import geojson
from fastkml.geometry import LineString
from pyproj import Transformer

# ETRS89-extended / LCC Europe is the default projection
DEFAULT_PROJECTION = "EPSG:3034"
DEFAULT_CENTER_COORDS = 4115023.91, 3536037.64  # of EPSG 3034; somewhere off Norwegian coast

DEFAULT_GEO_REFERENCE = "EPSG:4326"

CANVAS_ORIENTATION = -1

transformer = Transformer.from_crs(DEFAULT_PROJECTION, DEFAULT_GEO_REFERENCE)


def convert_multiple_canvas_coords_to_lonlat(*coords: tuple[str | float, str | float]) -> tuple[tuple[float, float], ...]:
    """
    Convert Cartesian coordinates to longitude and latitude.

    :param coords: array of coordinate pairs (X,Y) [, (X1, Y1)...] on some canvas
    :return: Tuple of longitude and latitude pairs.
    """
    return tuple(_convert_canvas_coords_to_lonlat(coord) for coord in coords)


def _convert_canvas_coords_to_lonlat(coord: tuple[str | float, str | float]) -> tuple[float, float]:
    """
    Convert a single coordinate pair from Cartesian (on canvas) to longitude and latitude.
    Note that the ordering conventions for coordinates differ...
    :param coord: Coordinate pair (X, Y) on Canvas
    :return: Converted coordinate pair (longitude, latitude)
    """
    return transformer.transform(*_convert_canvas_coords_to_projection(coord))


def _convert_canvas_coords_to_projection(canvas_coord: tuple[str | float, str | float]) -> tuple[float, float]:
    return CANVAS_ORIENTATION * float(canvas_coord[1]) + DEFAULT_CENTER_COORDS[1], \
           float(canvas_coord[0]) + DEFAULT_CENTER_COORDS[0]


def create_geojson_linestring(source: tuple[str | float, str | float], target: tuple[str | float, str | float],
                              *waypoints: tuple[str | float, str | float]) -> LineString:
    """
    Create a GeoJSON LineString from source, target, and optional waypoints.

    :param source: (X, Y) coordinate pair (on canvas) for the source.
    :param target: (X, Y) coordinate pair (on canvas) for the target.
    :param waypoints: Optional waypoints between source and target.
    :return: GeoJSON LineString object.
    """
    way_coords = (
        convert_multiple_canvas_coords_to_lonlat(source),
        *convert_multiple_canvas_coords_to_lonlat(*waypoints),
        convert_multiple_canvas_coords_to_lonlat(target)
    )
    return geojson.LineString(way_coords)


def create_geojson_point(x: float | str, y: float | str) -> geojson.Point:
    """
    Create a GeoJSON point from Cartesian coordinates on canvas.

    :param x: X coordinate.
    :param y: Y coordinate.
    :return: GeoJSON Point object.
    """
    return geojson.Point(_convert_canvas_coords_to_lonlat((float(x), float(y))))
